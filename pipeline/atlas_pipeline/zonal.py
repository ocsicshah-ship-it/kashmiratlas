"""Zonal aggregation of source rasters to H3 cells (Phase 1+).

Phase 0 uses synthetic.py instead of this module. The interface below is what the
real ingestion implements: build cell-boundary geometries once, then for each raster
run zonal statistics (mean for continuous bands, modal class + histogram for
categorical land cover) and merge the results into each cell's raw-parameter dict.

The heavy geospatial dependencies (rasterio, geopandas, exactextract) are optional
extras — install with `pip install -e .[raster]` before using this module.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import h3

from .cells import Cell


def cell_boundary_geojson(cell: Cell) -> dict:
    """GeoJSON Polygon (lng, lat order) for an H3 cell, for zonal extraction."""
    ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(cell.h3_index)]
    ring.append(ring[0])
    return {"type": "Polygon", "coordinates": [ring]}


def zonal_raw(cells: Iterable[Cell], rasters: dict[str, Path]) -> dict[str, dict]:
    """Return {h3_index: raw_params} from zonal stats over the given rasters.

    `rasters` maps a logical name (e.g. 'dem', 'worldcover', 'ghi') to a GeoTIFF
    path. Implemented in Phase 1; raises until then so callers fail loudly rather
    than silently producing empty data.
    """
    raise NotImplementedError(
        "Raster zonal aggregation is a Phase-1 task. For Phase 0 run the pipeline "
        "with --synthetic to generate scores without rasters."
    )
