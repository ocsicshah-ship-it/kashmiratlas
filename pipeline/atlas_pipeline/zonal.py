"""Zonal aggregation of source rasters to H3 cells (Phase 1+).

Aggregates DEM / land-cover / solar rasters onto each H3 cell: area-weighted mean
for continuous bands, modal class for categorical land cover. Phase 0 uses
synthetic.py instead; this module is used once real rasters are available.

Heavy geospatial deps (rasterio) are an optional extra:  pip install -e .[raster]
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import h3
import numpy as np

from .cells import Cell


def cell_boundary_geojson(cell_or_index: Cell | str) -> dict:
    """GeoJSON Polygon (lng, lat order) for an H3 cell, for zonal extraction."""
    idx = cell_or_index.h3_index if isinstance(cell_or_index, Cell) else cell_or_index
    ring = [[lng, lat] for lat, lng in h3.cell_to_boundary(idx)]
    ring.append(ring[0])
    return {"type": "Polygon", "coordinates": [ring]}


def _zonal_one(src, geom: dict, categorical: bool) -> float | int | None:
    """Mean (continuous) or modal class (categorical) of a raster within a polygon."""
    from rasterio.mask import mask as rio_mask

    try:
        out, _ = rio_mask(src, [geom], crop=True, filled=False)
    except ValueError:
        return None  # polygon does not overlap the raster
    band = out[0]
    data = band.compressed() if hasattr(band, "compressed") else band[~np.isnan(band)]
    if data.size == 0:
        return None
    if categorical:
        values, counts = np.unique(data, return_counts=True)
        return int(values[int(np.argmax(counts))])
    return float(np.mean(data))


def zonal_raw(
    cells: Iterable[Cell],
    rasters: dict[str, Path],
    categorical: set[str] | None = None,
) -> dict[str, dict]:
    """Return {h3_index: {raster_name: value}} from zonal stats over the rasters.

    `rasters` maps a logical name (e.g. 'elevation_m', 'landcover', 'ghi_kwh_m2_day')
    to a GeoTIFF path. `categorical` names the rasters aggregated by modal class.
    """
    import rasterio

    categorical = categorical or set()
    cells = list(cells)
    out: dict[str, dict] = {c.h3_index: {} for c in cells}

    for name, path in rasters.items():
        is_cat = name in categorical
        with rasterio.open(path) as src:
            for cell in cells:
                geom = cell_boundary_geojson(cell)
                val = _zonal_one(src, geom, is_cat)
                if val is not None:
                    out[cell.h3_index][name] = val
    return out


def terrain_from_dem(cells: Iterable[Cell], dem_path: Path, work_dir: Path) -> dict[str, dict]:
    """Per-cell {elevation_m, slope_deg, aspect_deg} zonal-aggregated from a DEM.

    Derives slope/aspect rasters from the DEM once, then zonal-aggregates all three
    bands onto the H3 cells. Returns {h3_index: terrain_dict}.
    """
    cells = list(cells)
    sa = derive_slope_aspect(Path(dem_path), Path(work_dir))
    stats = zonal_raw(cells, {"elevation_m": Path(dem_path), **sa})
    # keep only cells that actually overlapped the DEM
    return {h3: t for h3, t in stats.items() if "elevation_m" in t}


def derive_slope_aspect(dem_path: Path, out_dir: Path) -> dict[str, Path]:
    """Derive slope (deg) and aspect (deg) GeoTIFFs from a DEM via numpy gradient.

    Returns {'slope_deg': path, 'aspect_deg': path}. Uses a simple Horn-style
    gradient; for production prefer gdaldem/richdem.
    """
    import math

    import rasterio

    out_dir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dem_path) as src:
        z = src.read(1).astype("float64")
        px = src.transform.a            # x pixel size (units of the CRS)
        py = -src.transform.e           # y pixel size
        # DEM elevation is in metres; if the CRS is geographic the pixel spacing is
        # in degrees, so convert to metres before taking the gradient — otherwise
        # slope saturates near 90°.
        if src.crs and src.crs.is_geographic:
            lat0 = math.radians((src.bounds.top + src.bounds.bottom) / 2)
            px = px * 111_320.0 * math.cos(lat0)
            py = py * 110_540.0
        dzdx, dzdy = np.gradient(z, px, py)
        slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
        aspect = (np.degrees(np.arctan2(dzdy, -dzdx)) + 360) % 360
        profile = src.profile
        profile.update(dtype="float32", count=1)
        paths = {}
        for nm, arr in (("slope_deg", slope), ("aspect_deg", aspect)):
            p = out_dir / f"{nm}.tif"
            with rasterio.open(p, "w", **profile) as dst:
                dst.write(arr.astype("float32"), 1)
            paths[nm] = p
    return paths
