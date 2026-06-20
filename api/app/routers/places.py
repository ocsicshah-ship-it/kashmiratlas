"""Place endpoints: fuzzy search + overlap-weighted aggregated profile."""

from __future__ import annotations

import unicodedata

from fastapi import APIRouter, HTTPException, Query

from ..db import pool
from ..schemas import PlaceProfile, PlaceSearchResult

router = APIRouter(tags=["places"])


def _normalize(q: str) -> str:
    nkfd = unicodedata.normalize("NFKD", q)
    return "".join(c for c in nkfd if not unicodedata.combining(c)).lower().strip()


@router.get("/places/search", response_model=list[PlaceSearchResult])
async def search_places(q: str = Query(..., min_length=1), limit: int = 10):
    """Trigram fuzzy search over place names."""
    needle = _normalize(q)
    async with pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT place_id, name, kind, district
                FROM named_place
                WHERE name_normalized %% %s OR name_normalized LIKE %s
                ORDER BY similarity(name_normalized, %s) DESC
                LIMIT %s
                """,
                (needle, f"%{needle}%", needle, limit),
            )
            rows = await cur.fetchall()
    return [PlaceSearchResult(**r) for r in rows]


@router.get("/place/{place_id}", response_model=PlaceProfile)
async def place_profile(place_id: int):
    """Overlap-weighted 360 profile for a place plus its constituent cells."""
    async with pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT place_id, name, kind, district, population,
                       ST_XMin(geom::geometry) AS min_lng, ST_YMin(geom::geometry) AS min_lat,
                       ST_XMax(geom::geometry) AS max_lng, ST_YMax(geom::geometry) AS max_lat
                FROM named_place WHERE place_id = %s
                """,
                (place_id,),
            )
            place = await cur.fetchone()
            if place is None:
                raise HTTPException(status_code=404, detail=f"No place {place_id}")

            # Overlap-weighted mean of every domain score across the place's cells.
            await cur.execute(
                """
                SELECT key,
                       round(sum((val)::numeric * pc.overlap_fraction)
                             / nullif(sum(pc.overlap_fraction), 0)) AS wmean
                FROM place_cell pc
                JOIN grid_cell g USING (h3_index)
                CROSS JOIN LATERAL jsonb_each_text(g.scores) AS s(key, val)
                WHERE pc.place_id = %s
                GROUP BY key
                """,
                (place_id,),
            )
            scores = {r["key"]: int(r["wmean"]) for r in await cur.fetchall()}

            await cur.execute(
                "SELECT h3_index FROM place_cell WHERE place_id = %s", (place_id,)
            )
            cell_ids = [r["h3_index"] for r in await cur.fetchall()]

    return PlaceProfile(
        place_id=place["place_id"],
        name=place["name"],
        kind=place["kind"],
        district=place["district"],
        population=place["population"],
        cell_count=len(cell_ids),
        bbox=[place["min_lng"], place["min_lat"], place["max_lng"], place["max_lat"]],
        scores=scores,
        cell_ids=cell_ids,
    )
