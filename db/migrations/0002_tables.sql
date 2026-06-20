-- 0002_tables.sql
-- The three core tables. Deliberately NO hexagon polygon is stored on grid_cell:
-- the frontend reconstructs hex geometry on the GPU from the H3 index, and the
-- pipeline derives boundaries on demand from h3-pg. We keep only the centroid for
-- point/radius queries.

-- ── Layer 1: the H3 res-9 grid ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grid_cell (
    h3_index     TEXT PRIMARY KEY,                 -- res-9 cell, string form (e.g. '89...ffff')
    h3_res7      TEXT NOT NULL,                     -- precomputed parent for zoom roll-up
    h3_res8      TEXT NOT NULL,                     -- precomputed parent for zoom roll-up
    centroid     geography(Point, 4326) NOT NULL,
    elevation_m  REAL,                              -- promoted hot column (ordering/filtering)
    raw          JSONB NOT NULL DEFAULT '{}'::jsonb, -- raw zonal parameters per cell
    scores       JSONB NOT NULL DEFAULT '{}'::jsonb, -- {domain: 0..100}
    confidence   SMALLINT,                          -- 0..100 data completeness
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS grid_cell_res7_idx ON grid_cell (h3_res7);
CREATE INDEX IF NOT EXISTS grid_cell_res8_idx ON grid_cell (h3_res8);
CREATE INDEX IF NOT EXISTS grid_cell_centroid_gix ON grid_cell USING gist (centroid);
-- GIN over scores lets us filter "cells where scores->>'solar' high" cheaply if needed.
CREATE INDEX IF NOT EXISTS grid_cell_scores_gin ON grid_cell USING gin (scores jsonb_path_ops);

-- ── Layer 2: named places (villages / tehsils / towns) ───────────────────────
CREATE TABLE IF NOT EXISTS named_place (
    place_id        BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    name_local      TEXT,                            -- script / local-language name
    name_normalized TEXT NOT NULL,                   -- lowercase, unaccented; for trigram search
    kind            TEXT NOT NULL DEFAULT 'village', -- village | town | tehsil | block
    district        TEXT,
    population      INTEGER,
    geom            geography(MultiPolygon, 4326) NOT NULL,
    centroid        geography(Point, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS named_place_geom_gix ON named_place USING gist (geom);
CREATE INDEX IF NOT EXISTS named_place_centroid_gix ON named_place USING gist (centroid);
CREATE INDEX IF NOT EXISTS named_place_name_trgm ON named_place USING gin (name_normalized gin_trgm_ops);

-- ── Junction: place <-> cell with overlap weighting ──────────────────────────
CREATE TABLE IF NOT EXISTS place_cell (
    place_id         BIGINT NOT NULL REFERENCES named_place (place_id) ON DELETE CASCADE,
    h3_index         TEXT   NOT NULL REFERENCES grid_cell (h3_index) ON DELETE CASCADE,
    overlap_fraction REAL   NOT NULL CHECK (overlap_fraction > 0 AND overlap_fraction <= 1),
    PRIMARY KEY (place_id, h3_index)
);

CREATE INDEX IF NOT EXISTS place_cell_h3_idx ON place_cell (h3_index);
