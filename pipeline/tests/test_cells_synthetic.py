"""Cell generation + synthetic-raw + end-to-end scoring tests."""

from __future__ import annotations

from pathlib import Path

import h3

from atlas_pipeline import scoring, synthetic
from atlas_pipeline.cells import cells_for_geojson
from atlas_pipeline.domains import DOMAIN_IDS

AOI = Path(__file__).resolve().parents[2] / "sample-data" / "budgam_pilot.geojson"
RUBRICS = scoring.load_rubrics(Path(__file__).resolve().parents[1] / "rubrics")


def test_polyfill_pilot():
    cells = cells_for_geojson(AOI, res=9)
    assert len(cells) > 1000  # the pilot corridor is sizeable
    c = cells[0]
    assert h3.get_resolution(c.h3_index) == 9
    assert c.h3_res8 == h3.cell_to_parent(c.h3_index, 8)
    assert c.h3_res7 == h3.cell_to_parent(c.h3_index, 7)
    assert 33.5 < c.lat < 34.2 and 74.4 < c.lng < 75.0


def test_synthetic_is_deterministic():
    cells = cells_for_geojson(AOI, res=9)
    a = synthetic.synth_raw(cells[0])
    b = synthetic.synth_raw(cells[0])
    assert a == b
    assert 1550 <= a["elevation_m"] <= 3300


def test_synthetic_scores_all_domains():
    cells = cells_for_geojson(AOI, res=9)[:200]
    for cell in cells:
        scores = scoring.score_cell(synthetic.synth_raw(cell), DOMAIN_IDS, RUBRICS)
        assert set(scores) == set(DOMAIN_IDS)
        assert all(0 <= v <= 100 for v in scores.values())
