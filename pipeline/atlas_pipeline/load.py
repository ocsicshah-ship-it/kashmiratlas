"""Load cells, places and the place<->cell join into PostGIS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import psycopg
import unicodedata

from .cells import Cell


def _normalize(name: str) -> str:
    nkfd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nkfd if not unicodedata.combining(c)).lower().strip()


def upsert_cells(
    conn: psycopg.Connection,
    cells: list[Cell],
    raw_by_id: dict[str, dict[str, Any]],
    scores_by_id: dict[str, dict[str, int]],
) -> int:
    """Insert/replace grid_cell rows. Returns the number of rows written."""
    rows = []
    for c in cells:
        raw = raw_by_id.get(c.h3_index, {})
        rows.append(
            (
                c.h3_index,
                c.h3_res7,
                c.h3_res8,
                c.lng,
                c.lat,
                raw.get("elevation_m"),
                json.dumps(raw),
                json.dumps(scores_by_id.get(c.h3_index, {})),
                raw.get("confidence"),
            )
        )

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO grid_cell
                (h3_index, h3_res7, h3_res8, centroid, elevation_m, raw, scores, confidence)
            VALUES
                (%s, %s, %s,
                 ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                 %s, %s::jsonb, %s::jsonb, %s)
            ON CONFLICT (h3_index) DO UPDATE SET
                h3_res7 = EXCLUDED.h3_res7,
                h3_res8 = EXCLUDED.h3_res8,
                centroid = EXCLUDED.centroid,
                elevation_m = EXCLUDED.elevation_m,
                raw = EXCLUDED.raw,
                scores = EXCLUDED.scores,
                confidence = EXCLUDED.confidence,
                updated_at = now()
            """,
            rows,
        )
    conn.commit()
    return len(rows)


def load_places(conn: psycopg.Connection, geojson_path: str | Path) -> int:
    """Load named places from a GeoJSON FeatureCollection (Polygon/MultiPolygon)."""
    data = json.loads(Path(geojson_path).read_text())
    written = 0
    with conn.cursor() as cur:
        cur.execute("TRUNCATE named_place RESTART IDENTITY CASCADE")
        for feat in data["features"]:
            props = feat.get("properties", {})
            name = props["name"]
            geom_json = json.dumps(feat["geometry"])
            cur.execute(
                """
                INSERT INTO named_place
                    (name, name_local, name_normalized, kind, district, population, geom, centroid)
                VALUES
                    (%s, %s, %s, %s, %s, %s,
                     ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))::geography,
                     ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))::geography)
                """,
                (
                    name,
                    props.get("name_local"),
                    _normalize(name),
                    props.get("kind", "village"),
                    props.get("district"),
                    props.get("population"),
                    geom_json,
                    geom_json,
                ),
            )
            written += 1
    conn.commit()
    return written


def rebuild_place_cell(conn: psycopg.Connection) -> int:
    """Recompute the place<->cell junction with overlap fractions.

    Cell polygons are derived on the fly from the H3 index via h3-pg
    (h3_cell_to_boundary_geometry); we never store them. Overlap fraction is the
    planar intersection-area ratio (adequate for weighting at this scale).
    """
    with conn.cursor() as cur:
        cur.execute("TRUNCATE place_cell")
        cur.execute(
            """
            INSERT INTO place_cell (place_id, h3_index, overlap_fraction)
            SELECT p.place_id, g.h3_index,
                   GREATEST(0.0001, LEAST(1.0,
                       ST_Area(ST_Intersection(cell.geom, pg.geom)) /
                       NULLIF(ST_Area(cell.geom), 0)))::real
            FROM named_place p
            JOIN LATERAL (SELECT p.geom::geometry AS geom) pg ON TRUE
            JOIN grid_cell g ON TRUE
            JOIN LATERAL (
                SELECT h3_cell_to_boundary_geometry(g.h3_index::h3index) AS geom
            ) cell ON ST_Intersects(cell.geom, pg.geom)
            """
        )
        written = cur.rowcount
    conn.commit()
    return written


def refresh_rollups(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT refresh_grid_rollups()")
    conn.commit()
