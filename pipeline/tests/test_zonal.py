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


def _write_sloped_raster(path, bounds, grade, size=300):
    """Geographic DEM with a known constant grade (rise/run) in the +x direction."""
    import math

    from rasterio.transform import from_bounds

    minx, miny, maxx, maxy = bounds
    transform = from_bounds(minx, miny, maxx, maxy, size, size)
    lat0 = math.radians((miny + maxy) / 2)
    px_m = transform.a * 111_320.0 * math.cos(lat0)  # metres per pixel in x
    cols = np.arange(size)
    z = np.tile(cols * grade * px_m, (size, 1)).astype("float32")  # rise = grade * run
    with rasterio.open(path, "w", driver="GTiff", height=size, width=size, count=1,
                       dtype="float32", crs="EPSG:4326", transform=transform) as dst:
        dst.write(z, 1)


def test_slope_units_are_degrees_not_saturated(tmp_path):
    import math

    p = tmp_path / "sloped.tif"
    _write_sloped_raster(p, (74.5, 33.7, 74.9, 34.0), grade=0.10)  # 10% grade -> ~5.71°
    sa = zonal.derive_slope_aspect(p, tmp_path / "sa")
    with rasterio.open(sa["slope_deg"]) as s:
        slope = s.read(1)[10:-10, 10:-10]  # trim edge effects
    mean_slope = float(np.mean(slope))
    assert 4.5 < mean_slope < 7.0, mean_slope  # near atan(0.10)=5.71°, NOT ~90°
    assert mean_slope == pytest.approx(math.degrees(math.atan(0.10)), abs=1.0)


def test_terrain_from_dem_flat(tmp_path):
    cells = cells_for_geojson(AOI, res=9)[:20]
    p = tmp_path / "flat2000.tif"
    _write_constant_raster(p, 2000.0, (74.5, 33.7, 74.9, 34.0))
    terr = zonal.terrain_from_dem(cells, p, tmp_path / "w")
    assert terr, "no cells got terrain"
    for t in terr.values():
        assert abs(t["elevation_m"] - 2000.0) < 1.0
        assert t["slope_deg"] < 1.0  # flat surface


def test_modal_landcover_maps_worldcover(tmp_path):
    cells = cells_for_geojson(AOI, res=9)[:15]
    p = tmp_path / "wc.tif"
    _write_constant_raster(p, 10.0, (74.5, 33.7, 74.9, 34.0))  # WorldCover 10 = tree cover
    lc = zonal.modal_landcover(cells, p)
    assert lc, "no cells got land cover"
    assert set(lc.values()) == {"forest"}  # class 10 -> forest


def test_synth_raw_honours_real_terrain():
    from atlas_pipeline import synthetic
    cell = cells_for_geojson(AOI, res=9)[0]
    over = {"elevation_m": 1650.0, "slope_deg": 7.0, "aspect_deg": 180.0}
    raw = synthetic.synth_raw(cell, over)
    assert raw["elevation_m"] == 1650.0
    assert raw["slope_deg"] == 7.0
    assert raw["aspect_south_factor"] == 1.0  # due-south aspect
    assert raw["confidence"] == 55  # real-terrain confidence
    # modelled (no terrain) differs and is low-confidence
    assert synthetic.synth_raw(cell)["confidence"] == 35
