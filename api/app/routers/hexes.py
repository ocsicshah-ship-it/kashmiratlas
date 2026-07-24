"""Bulk hex+score serving with zoom-based resolution roll-up.

We never serve polygons — only the H3 index + score map. The frontend's deck.gl
H3HexagonLayer reconstructs geometry on the GPU. Low zoom serves res-7/res-8
aggregates (materialized views) to keep payloads small.

Default response is JSON; pass ?format=arrow for a compact columnar Arrow IPC stream
(h3 string column + one int column per domain) — the plan's "single cached blob".
"""

from __future__ import annotations

import io

from fastapi import APIRouter, Query
from fastapi.responses import Response

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


async def _query(zoom: float, bbox: str | None):
    res = _resolution_for_zoom(zoom)
    source = _SOURCE[res]
    where = ""
    params: list = []
    # bbox filtering is applied only at res-9 (which stores a centroid). The res-7/8
    # aggregate views are tiny at valley scale, so we return them whole.
    if bbox and res == 9:
        min_lng, min_lat, max_lng, max_lat = (float(x) for x in bbox.split(","))
        where = " WHERE centroid && ST_MakeEnvelope(%s, %s, %s, %s, 4326)::geography"
        params = [min_lng, min_lat, max_lng, max_lat]

    sql = f"SELECT h3_index, scores FROM {source}{where}"
    async with pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
    return res, rows


@router.get("/hexes")
async def hexes(
    zoom: float = Query(12, ge=0, le=24),
    bbox: str | None = Query(None, description="'minLng,minLat,maxLng,maxLat' viewport filter."),
    format: str = Query("json", pattern="^(json|arrow)$"),
):
    """Return all hexes (optionally within bbox) at the resolution for this zoom."""
    res, rows = await _query(zoom, bbox)

    if format == "arrow":
        import pyarrow as pa
        import pyarrow.ipc as ipc

        domains = sorted({k for r in rows for k in (r["scores"] or {})})
        cols: dict[str, list] = {"h3": [r["h3_index"] for r in rows]}
        for d in domains:
            cols[d] = [int((r["scores"] or {}).get(d, 0)) for r in rows]
        table = pa.table(cols)
        sink = io.BytesIO()
        with ipc.new_stream(sink, table.schema) as writer:
            writer.write_table(table)
        return Response(
            content=sink.getvalue(),
            media_type="application/vnd.apache.arrow.stream",
            headers={"X-Atlas-Resolution": str(res), "X-Atlas-Count": str(len(rows))},
        )

    hexes = [HexFeature(h3=r["h3_index"], scores=r["scores"] or {}) for r in rows]
    return HexCollection(resolution=res, count=len(hexes), hexes=hexes)
