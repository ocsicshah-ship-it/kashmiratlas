-- 0003_agg_views.sql
-- Zoom roll-up: average each domain score across child cells grouped by parent.
-- Scores live in JSONB, so we provide an aggregate that means-merges score maps,
-- then materialize res-8 and res-7 views the API serves at lower zoom levels.

-- Aggregate state for averaging score maps across rows.
CREATE OR REPLACE FUNCTION jsonb_scores_accum(state jsonb, next jsonb)
RETURNS jsonb LANGUAGE sql IMMUTABLE AS $$
    -- Accumulate per-key running sum + count as {key: [sum, count]}.
    SELECT coalesce(jsonb_object_agg(key,
              jsonb_build_array(
                  coalesce((state -> key ->> 0)::numeric, 0) + val,
                  coalesce((state -> key ->> 1)::numeric, 0) + 1)), state)
    FROM jsonb_each_text(next) AS t(key, txt)
    CROSS JOIN LATERAL (SELECT (txt)::numeric AS val) v
$$;

CREATE OR REPLACE FUNCTION jsonb_scores_final(state jsonb)
RETURNS jsonb LANGUAGE sql IMMUTABLE AS $$
    SELECT jsonb_object_agg(key, round((arr ->> 0)::numeric / (arr ->> 1)::numeric))
    FROM jsonb_each(state) AS t(key, arr)
$$;

DROP AGGREGATE IF EXISTS jsonb_scores_avg(jsonb);
CREATE AGGREGATE jsonb_scores_avg(jsonb) (
    sfunc     = jsonb_scores_accum,
    stype     = jsonb,
    initcond  = '{}',
    finalfunc = jsonb_scores_final
);

-- res-8 roll-up
CREATE MATERIALIZED VIEW IF NOT EXISTS grid_cell_res8 AS
SELECT
    h3_res8                              AS h3_index,
    count(*)                             AS child_count,
    avg(elevation_m)::real               AS elevation_m,
    jsonb_scores_avg(scores)             AS scores
FROM grid_cell
GROUP BY h3_res8;
CREATE UNIQUE INDEX IF NOT EXISTS grid_cell_res8_pk ON grid_cell_res8 (h3_index);

-- res-7 roll-up
CREATE MATERIALIZED VIEW IF NOT EXISTS grid_cell_res7 AS
SELECT
    h3_res7                              AS h3_index,
    count(*)                             AS child_count,
    avg(elevation_m)::real               AS elevation_m,
    jsonb_scores_avg(scores)             AS scores
FROM grid_cell
GROUP BY h3_res7;
CREATE UNIQUE INDEX IF NOT EXISTS grid_cell_res7_pk ON grid_cell_res7 (h3_index);

-- Refresh both roll-ups. The pipeline calls this after each load.
CREATE OR REPLACE FUNCTION refresh_grid_rollups()
RETURNS void LANGUAGE sql AS $$
    REFRESH MATERIALIZED VIEW grid_cell_res8;
    REFRESH MATERIALIZED VIEW grid_cell_res7;
$$;
