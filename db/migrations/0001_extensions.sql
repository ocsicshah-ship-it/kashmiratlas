-- 0001_extensions.sql
-- Spatial + H3 + fuzzy-search extensions. Idempotent.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS h3;
CREATE EXTENSION IF NOT EXISTS h3_postgis;   -- PostGIS <-> H3 bridge (boundaries, polyfill)
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- trigram fuzzy place search
