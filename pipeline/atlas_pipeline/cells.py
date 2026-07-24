"""Generate the H3 cell set for an area of interest.

GeoJSON stores coordinates as [lng, lat]; H3 v4 LatLngPoly expects (lat, lng).
We flip on the way in. Output cells carry their res-7 / res-8 parents and centroid
so the loader can populate grid_cell directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import h3


@dataclass(frozen=True)
class Cell:
    h3_index: str
    h3_res7: str
    h3_res8: str
    lat: float
    lng: float


def _rings_from_geojson_geometry(geometry: dict) -> list[list[tuple[float, float]]]:
    """Return a list of (lat, lng) outer rings from a Polygon/MultiPolygon geometry."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    polys = coords if gtype == "MultiPolygon" else [coords]
    rings: list[list[tuple[float, float]]] = []
    for poly in polys:
        outer = poly[0]  # ignore holes for AOI definition
        rings.append([(lat, lng) for lng, lat in outer])
    return rings


def cells_for_geojson(path: str | Path, res: int = 9) -> list[Cell]:
    """Polyfill every feature in a GeoJSON file at the given resolution."""
    data = json.loads(Path(path).read_text())
    features = data.get("features", [data]) if data.get("type") != "Feature" else [data]

    indices: set[str] = set()
    for feature in features:
        geometry = feature.get("geometry", feature)
        for ring in _rings_from_geojson_geometry(geometry):
            shape = h3.LatLngPoly(ring)
            indices.update(h3.polygon_to_cells(shape, res))

    cells: list[Cell] = []
    for idx in indices:
        lat, lng = h3.cell_to_latlng(idx)
        cells.append(
            Cell(
                h3_index=idx,
                h3_res7=h3.cell_to_parent(idx, 7),
                h3_res8=h3.cell_to_parent(idx, 8),
                lat=lat,
                lng=lng,
            )
        )
    return cells
