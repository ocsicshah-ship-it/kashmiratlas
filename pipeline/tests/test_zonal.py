"""Zonal-aggregation tests (Phase 1). Skipped unless rasterio is installed."""

from __future__ import annotations

from pathlib import Path

import pytest

rasterio = pytest.importorskip("rasterio")

import numpy as np  # noqa: E402

from atlas_pipeline import zonal  # noqa: E402
from atlas_pipeline.cells import cells_for_geojson  # noqa: E402

AOI = Path(__file__).resolve().parents[2] / "sample-data" / "budgam_pilot.geojson"


def _write_constant_raster(path: Path, value: float, bounds, size=200):
    from rasterio.transform import from_bounds

    minx, miny, maxx, maxy = bounds
    transform = from_bounds(minx, miny, maxx, maxy, size, size)
    data = np.full((size, size), value, dtype="float32")
    with rasterio.open(
        path, "w", driver="GTiff", height=size, width=size, count=1,
        dtype="float32", crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(data, 1)


def test_zonal_mean_constant(tmp_path):
    cells = cells_for_geojson(AOI, res=9)[:25]
    rpath = tmp_path / "const.tif"
    _write_constant_raster(rpath, 2000.0, (74.5, 33.7, 74.9, 34.0))
    out = zonal.zonal_raw(cells, {"elevation_m": rpath})
    sampled = [v["elevation_m"] for v in out.values() if "elevation_m" in v]
    assert sampled, "no cells overlapped the test raster"
    assert all(abs(v - 2000.0) < 1e-3 for v in sampled)


def test_cell_boundary_geojson_closed():
    cells = cells_for_geojson(AOI, res=9)
    gj = zonal.cell_boundary_geojson(cells[0])
    ring = gj["coordinates"][0]
    assert ring[0] == ring[-1]  # closed
    assert len(ring) == 7  # hexagon + closing vertex
