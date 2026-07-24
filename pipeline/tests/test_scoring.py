"""Scoring-registry unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_pipeline import scoring
from atlas_pipeline.domains import DOMAIN_IDS, score_band

RUBRICS = scoring.load_rubrics(Path(__file__).resolve().parents[1] / "rubrics")


def _base_raw(**over):
    raw = {
        "elevation_m": 1650, "slope_deg": 8, "aspect_south_factor": 0.8, "relief_m": 300,
        "soil_type": "karewa", "soil_ph": 5.0, "drainage_class": 4, "landcover": "cropland",
        "geology_unit": "limestone-shale", "orchard_present": True, "shade_fraction": 0.4,
        "ghi_kwh_m2_day": 5.2, "snow_cover_fraction": 0.2, "snow_cover_days": 40,
        "chilling_hours": 1200, "summer_air_temp_c": 26, "winter_mean_temp_c": -9,
        "perennial_stream": True, "near_water": True, "stream_gradient": 0.02,
        "est_power_kw": 120, "gross_head_m": 60, "river_order": 4,
        "summer_water_temp_c": 13, "annual_water_temp_c": 12, "water_temp_stability": 0.9,
        "spring_present": True, "spring_discharge_cumec": 0.03, "spring_decline_fraction": 0.1,
        "spring_cluster_size": 5, "glacier_dependence": 0.3, "shrine_proximity": 0.8,
        "festival_site": True, "mining_pressure": 0.1, "carrying_capacity_su": 3,
        "landslide": 30, "flood_fraction": 0.1, "market_access_km": 8, "grid_proximity": 0.8,
        "distance_to_loc_km": 30, "pass_closure_fraction": 0.2, "bortle": 3,
        "snow_leopard_density": 0, "confidence": 35,
    }
    raw.update(over)
    return raw


def test_every_domain_scores_in_range():
    scores = scoring.score_cell(_base_raw(), DOMAIN_IDS, RUBRICS)
    assert set(scores) == set(DOMAIN_IDS)
    for d, v in scores.items():
        assert isinstance(v, int), d
        assert 0 <= v <= 100, (d, v)


def test_all_domains_have_bespoke_scorer():
    # No domain should silently fall back to the generic hint scorer.
    assert set(DOMAIN_IDS).issubset(set(scoring.registered_domains()))


def test_saffron_hard_gated_on_karewa():
    on = scoring.score_cell(_base_raw(soil_type="karewa", elevation_m=1640), ["saffron"], RUBRICS)
    off = scoring.score_cell(_base_raw(soil_type="alluvial"), ["saffron"], RUBRICS)
    assert on["saffron"] > 50
    assert off["saffron"] <= 20


def test_wasabi_disqualified_by_warm_water():
    warm = scoring.score_cell(_base_raw(annual_water_temp_c=21), ["wasabi"], RUBRICS)
    cold = scoring.score_cell(_base_raw(annual_water_temp_c=12), ["wasabi"], RUBRICS)
    assert warm["wasabi"] == 0
    assert cold["wasabi"] > 40


def test_wasabi_needs_water():
    dry = scoring.score_cell(_base_raw(spring_present=False, perennial_stream=False), ["wasabi"], RUBRICS)
    assert dry["wasabi"] == 0


def test_trek_inverts_with_warm_winter():
    warm = scoring.score_cell(_base_raw(winter_mean_temp_c=-3), ["tourism_trek"], RUBRICS)
    cold = scoring.score_cell(_base_raw(winter_mean_temp_c=-18, relief_m=600), ["tourism_trek"], RUBRICS)
    assert cold["tourism_trek"] > warm["tourism_trek"]


@pytest.mark.parametrize("score,band", [(0, 1), (20, 1), (21, 2), (55, 3), (75, 4), (95, 5)])
def test_score_band(score, band):
    assert score_band(score) == band
