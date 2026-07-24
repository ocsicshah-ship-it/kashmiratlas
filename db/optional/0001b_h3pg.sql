-- OPTIONAL: only if you build the h3-pg image (db/optional/Dockerfile.h3pg).
-- The atlas does NOT require these; H3 math runs in Python. Installing h3-pg lets
-- you do H3 lookups in SQL (e.g. ad-hoc point->cell queries).
CREATE EXTENSION IF NOT EXISTS h3;
CREATE EXTENSION IF NOT EXISTS h3_postgis;
