-- 0001_extensions.sql
-- Spatial + fuzzy-search extensions. Idempotent.
--
-- NOTE: H3 index math (lat/lng -> cell, cell -> parent, cell -> boundary) is done
-- in Python with h3-py in the pipeline and API, so the database needs only stock
-- PostGIS — no custom h3-pg image required. If you DO install h3-pg, the optional
-- migration db/optional/0001b_h3pg.sql adds the SQL-side helpers.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- trigram fuzzy place search
