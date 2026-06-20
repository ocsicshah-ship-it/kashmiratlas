"""Bulk hex+score serving with zoom-based resolution roll-up.

We never serve polygons — only the H3 index + score map. The frontend's deck.gl
H3HexagonLayer reconstructs geometry on the GPU. Low zoom serves res-7/res-8
aggregates (materialized views) to keep payloads small.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..db import pool
from ..schemas import HexCollection, HexFeature

router = APIRouter(tags=["hexes"])


def _resolution_for_zoom(zoom: float) -> int:
    if zoom >= 12:
        return 9
    if zoom >= 10:
        return 8
    return 7


_SOURCE = {9: "grid_cell", 8: "grid_cell_res8", 7: "grid_cell_res7"}


@router.get("/hexes", response_model=HexCollection)
async def hexes(
    zoom: float = Query(12, ge=0, le=24),
    bbox: str | None = Query(
        None, description="Optional 'minLng,minLat,maxLng,maxLat' viewport filter."
    ),
):
    """Return all hexes (optionally within bbox) at the resolution for this zoom."""
    res = _resolution_for_zoom(zoom)
    source = _SOURCE[res]

    where = ""
    params: list = []
    # bbox filtering is applied only at res-9 (which stores a centroid). The res-7/8
    # aggregate views are tiny at valley scale, so we return them whole and let the
    # client cull. This is the "single cached blob" delivery from the plan.
    if bbox and res == 9:
        min_lng, min_lat, max_lng, max_lat = (float(x) for x in bbox.split(","))
        where = " WHERE centroid && ST_MakeEnvelope(%s, %s, %s, %s, 4326)::geography"
        params = [min_lng, min_lat, max_lng, max_lat]

    sql = f"SELECT h3_index, scores FROM {source}{where}"
    async with pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()

    hexes = [HexFeature(h3=r["h3_index"], scores=r["scores"] or {}) for r in rows]
    return HexCollection(resolution=res, count=len(hexes), hexes=hexes)
