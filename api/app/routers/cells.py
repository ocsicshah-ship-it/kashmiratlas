"""Cell endpoints: point query and cell-by-id profile."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..db import pool
from ..schemas import CellProfile, PlaceRef

router = APIRouter(tags=["cells"])

_CELL_SQL = """
    SELECT g.h3_index,
           ST_X(g.centroid::geometry) AS lng,
           ST_Y(g.centroid::geometry) AS lat,
           g.elevation_m, g.confidence, g.scores, g.raw
    FROM grid_cell g
    WHERE g.h3_index = %s
"""

_PLACES_SQL = """
    SELECT p.place_id, p.name, pc.overlap_fraction
    FROM place_cell pc
    JOIN named_place p USING (place_id)
    WHERE pc.h3_index = %s
    ORDER BY pc.overlap_fraction DESC
"""


async def _build_profile(h3_index: str) -> CellProfile:
    async with pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(_CELL_SQL, (h3_index,))
            row = await cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail=f"No cell {h3_index}")
            await cur.execute(_PLACES_SQL, (h3_index,))
            places = await cur.fetchall()

    return CellProfile(
        h3_index=row["h3_index"],
        resolution=9,
        centroid=[row["lng"], row["lat"]],
        elevation_m=row["elevation_m"],
        confidence=row["confidence"],
        scores=row["scores"] or {},
        raw=row["raw"] or {},
        places=[PlaceRef(**p) for p in places],
    )


@router.get("/cell", response_model=CellProfile)
async def cell_by_point(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    """Resolve a lat/lng to its H3 res-9 cell and return the cell profile."""
    async with pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT h3_lat_lng_to_cell(POINT(%s, %s), 9)::text AS h3", (lng, lat)
            )
            row = await cur.fetchone()
    return await _build_profile(row["h3"])


@router.get("/cell/{h3_index}", response_model=CellProfile)
async def cell_by_id(h3_index: str):
    return await _build_profile(h3_index)
