"""Pluggable capability-scoring registry.

Each domain is a pure function ``(raw, cfg) -> 0..100`` registered by id. Thresholds
and weights live in YAML rubrics (pipeline/rubrics/*.yaml) so they can be tuned
without code changes. The pipeline stores BOTH the raw parameters and the computed
scores, so scores can be recomputed as rubrics improve.

Add a domain = add one ``@register`` function here + one rubric entry.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

Scorer = Callable[[dict[str, Any], dict[str, Any]], float]
_REGISTRY: dict[str, Scorer] = {}


def register(domain_id: str) -> Callable[[Scorer], Scorer]:
    def deco(fn: Scorer) -> Scorer:
        _REGISTRY[domain_id] = fn
        return fn

    return deco


def registered_domains() -> list[str]:
    return list(_REGISTRY)


# ── scoring helpers ──────────────────────────────────────────────────────────
def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def ramp(value: float | None, lo: float, hi: float) -> float:
    """Linear 0..1 ramp; None -> 0."""
    if value is None or hi == lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def trapezoid(value: float | None, a: float, b: float, c: float, d: float) -> float:
    """Plateau membership in [b, c], ramping up over [a, b], down over [c, d]. 0..1."""
    if value is None:
        return 0.0
    if value <= a or value >= d:
        return 0.0
    if b <= value <= c:
        return 1.0
    if value < b:
        return (value - a) / (b - a)
    return (d - value) / (d - c)


# ── domain scorers ───────────────────────────────────────────────────────────
@register("solar_pv")
def _solar(raw: dict, cfg: dict) -> float:
    ghi = ramp(raw.get("ghi_kwh_m2_day"), cfg.get("ghi_lo", 3.5), cfg.get("ghi_hi", 6.5))
    south = raw.get("aspect_south_factor", 0.6)  # 0..1, 1 = due south
    snow = raw.get("snow_cover_fraction", 0.2)  # 0..1
    slope_ok = 1.0 - ramp(raw.get("slope_deg"), cfg.get("slope_ideal", 25), cfg.get("slope_max", 45))
    return clamp(100 * ghi * (0.5 + 0.5 * south) * (1 - 0.6 * snow) * slope_ok)


@register("apple")
def _apple(raw: dict, cfg: dict) -> float:
    elev = trapezoid(raw.get("elevation_m"), 1300, 1600, 2200, 2700)
    chill = ramp(raw.get("chilling_hours"), cfg.get("chill_lo", 800), cfg.get("chill_hi", 1400))
    slope = 1.0 - ramp(raw.get("slope_deg"), 20, 40)
    sun = 0.5 + 0.5 * raw.get("aspect_south_factor", 0.6)
    return clamp(100 * (0.35 * elev + 0.30 * chill + 0.20 * slope + 0.15 * sun))


@register("saffron")
def _saffron(raw: dict, cfg: dict) -> float:
    # Hard-gated on karewa soil + low elevation + good drainage.
    if raw.get("soil_type") != "karewa":
        return clamp(15 * raw.get("aspect_south_factor", 0.5))
    elev = trapezoid(raw.get("elevation_m"), 1500, 1585, 1700, 1850)
    drain = ramp(raw.get("drainage_class"), 2, 5)
    flat = 1.0 - ramp(raw.get("slope_deg"), 3, 12)
    return clamp(100 * (0.5 * elev + 0.25 * drain + 0.25 * flat))


@register("hydro_micro")
def _hydro(raw: dict, cfg: dict) -> float:
    power_kw = raw.get("est_power_kw", 0.0)
    return clamp(100 * ramp(power_kw, 0, cfg.get("power_full_kw", 150)))


@register("aquaculture_trout")
def _trout(raw: dict, cfg: dict) -> float:
    if not raw.get("perennial_stream"):
        return 0.0
    temp = raw.get("summer_water_temp_c", 22.0)
    cold = 1.0 - ramp(temp, 16, 22)
    flow = ramp(raw.get("stream_gradient"), 0.005, 0.05)
    return clamp(100 * (0.7 * cold + 0.3 * flow))


@register("grazing")
def _grazing(raw: dict, cfg: dict) -> float:
    return clamp(100 * ramp(raw.get("carrying_capacity_su"), 0, cfg.get("su_full", 6)))


@register("construction")
def _construction(raw: dict, cfg: dict) -> float:
    base = 100.0
    base -= 60 * ramp(raw.get("slope_deg"), 5, 35)          # steep slope penalty
    base -= 40 * raw.get("flood_fraction", 0.0)             # floodplain penalty
    base -= 0.4 * raw.get("landslide", 0.0)                 # landslide penalty
    base -= 10                                              # Zone-V baseline down-weight
    return clamp(base)


@register("tourism")
def _tourism(raw: dict, cfg: dict) -> float:
    relief = ramp(raw.get("relief_m"), 50, 600)
    meadow = 1.0 if raw.get("landcover") in {"grassland", "meadow"} else 0.4
    water = 0.2 + 0.8 * (1.0 if raw.get("near_water") else 0.0)
    snow = ramp(raw.get("snow_cover_days"), 30, 150)
    return clamp(100 * (0.35 * relief + 0.25 * meadow + 0.2 * water + 0.2 * snow))


@register("agriculture")
def _agriculture(raw: dict, cfg: dict) -> float:
    # Composite of the staple/horticulture suitabilities for the cell.
    return clamp(
        0.4 * _apple(raw, {})
        + 0.3 * _paddy(raw, {})
        + 0.3 * _exotic_vegetables(raw, {})
    )


@register("paddy")
def _paddy(raw: dict, cfg: dict) -> float:
    if raw.get("elevation_m", 9999) > 1700:
        return clamp(10 * (1 - ramp(raw.get("slope_deg"), 2, 8)))
    flat = 1.0 - ramp(raw.get("slope_deg"), 1, 6)
    irrig = 1.0 if raw.get("near_water") else 0.4
    soil_ok = 1.0 if raw.get("soil_type") in {"sekil", "alluvial", "dazanlad"} else 0.5
    return clamp(100 * (0.5 * flat + 0.25 * irrig + 0.25 * soil_ok))


@register("stonefruit")
def _stonefruit(raw: dict, cfg: dict) -> float:
    elev = trapezoid(raw.get("elevation_m"), 1500, 1600, 2100, 2500)
    warm = 0.5 + 0.5 * raw.get("aspect_south_factor", 0.6)
    return clamp(100 * (0.6 * elev + 0.4 * warm))


@register("exotic_vegetables")
def _exotic_vegetables(raw: dict, cfg: dict) -> float:
    # Protected/peri-urban veg: needs gentle slope, water, market access.
    flat = 1.0 - ramp(raw.get("slope_deg"), 5, 25)
    water = 1.0 if raw.get("near_water") else 0.5
    access = 1.0 - ramp(raw.get("market_access_km"), 5, 40)
    elev = trapezoid(raw.get("elevation_m"), 1500, 1550, 2200, 2600)
    return clamp(100 * (0.3 * flat + 0.25 * water + 0.25 * access + 0.2 * elev))


@register("protected_cultivation")
def _protected_cultivation(raw: dict, cfg: dict) -> float:
    # Polyhouse siting: flat, sunny, accessible, frost-buffered low-mid elevation.
    flat = 1.0 - ramp(raw.get("slope_deg"), 3, 15)
    sun = ramp(raw.get("ghi_kwh_m2_day"), 3.5, 6.0)
    access = 1.0 - ramp(raw.get("market_access_km"), 5, 40)
    return clamp(100 * (0.45 * flat + 0.3 * sun + 0.25 * access))


@register("berry")
def _berry(raw: dict, cfg: dict) -> float:
    # Strawberry broad; blueberry needs acidic karewa (pH 4.5-5.5).
    ph = raw.get("soil_ph", 6.5)
    acid_bonus = trapezoid(ph, 4.0, 4.5, 5.5, 6.5)
    elev = trapezoid(raw.get("elevation_m"), 1500, 1550, 2000, 2400)
    drain = ramp(raw.get("drainage_class"), 2, 5)
    karewa = 1.0 if raw.get("soil_type") == "karewa" else 0.6
    return clamp(100 * (0.3 * elev + 0.25 * drain + 0.25 * acid_bonus + 0.2 * karewa))


@register("indigenous_landrace")
def _indigenous_landrace(raw: dict, cfg: dict) -> float:
    # Haakh (peri-urban rich soils) + nadru (lake/wetland floating beds).
    wetland = 1.0 if raw.get("landcover") in {"nambal", "wetland"} or raw.get("soil_type") == "nambal" else 0.0
    periurban = 1.0 - ramp(raw.get("market_access_km"), 2, 20)
    return clamp(100 * (0.5 * wetland + 0.5 * periurban * (raw.get("elevation_m", 9999) < 1700)))


# ── Specialty crops ──────────────────────────────────────────────────────────
@register("wasabi")
def _wasabi(raw: dict, cfg: dict) -> float:
    # Sawa wasabi: cold flowing spring water 8-18C (optimum 10-15C), shaded.
    if not raw.get("spring_present") and not raw.get("perennial_stream"):
        return 0.0
    temp = raw.get("annual_water_temp_c", 16.0)
    if temp > cfg.get("temp_disqualify", 20):
        return 0.0  # soft-rot / geothermal disqualifier
    thermal = trapezoid(temp, 6, 10, 15, 19)
    stable = ramp(raw.get("water_temp_stability", 0.5), 0.3, 1.0)
    discharge = ramp(raw.get("spring_discharge_cumec", 0), 0.01, 0.05)
    elev = trapezoid(raw.get("elevation_m"), 1500, 1876, 2266, 2400)
    shade = ramp(raw.get("shade_fraction", 0.4), 0.3, 0.8)
    return clamp(100 * (0.4 * thermal + 0.2 * stable + 0.15 * discharge + 0.15 * elev + 0.1 * shade))


@register("watercress")
def _watercress(raw: dict, cfg: dict) -> float:
    if not (raw.get("spring_present") or raw.get("perennial_stream")):
        return 0.0
    cold = 1.0 - ramp(raw.get("summer_water_temp_c"), 16, 24)
    flow = ramp(raw.get("stream_gradient"), 0.003, 0.03)
    return clamp(100 * (0.7 * cold + 0.3 * flow))


@register("lavender")
def _lavender(raw: dict, cfg: dict) -> float:
    # Sunny, well-drained slopes; karewa benches favoured (Aroma Mission).
    sun = 0.5 + 0.5 * raw.get("aspect_south_factor", 0.6)
    drain = ramp(raw.get("drainage_class"), 3, 5)
    elev = trapezoid(raw.get("elevation_m"), 1500, 1600, 2100, 2500)
    karewa = 1.0 if raw.get("soil_type") in {"karewa", "mountain"} else 0.7
    return clamp(100 * (0.35 * sun + 0.25 * drain + 0.25 * elev + 0.15 * karewa))


@register("culinary_herbs")
def _culinary_herbs(raw: dict, cfg: dict) -> float:
    # Mediterranean-climate match; protected/peri-urban favoured.
    elev = trapezoid(raw.get("elevation_m"), 1500, 1550, 2200, 2600)
    sun = ramp(raw.get("ghi_kwh_m2_day"), 3.5, 6.0)
    access = 1.0 - ramp(raw.get("market_access_km"), 5, 40)
    return clamp(100 * (0.4 * elev + 0.3 * sun + 0.3 * access))


@register("hops")
def _hops(raw: dict, cfg: dict) -> float:
    # ~34N latitude climate match; deep soil, sun, moderate elevation.
    elev = trapezoid(raw.get("elevation_m"), 1500, 1550, 2000, 2400)
    sun = 0.5 + 0.5 * raw.get("aspect_south_factor", 0.6)
    drain = ramp(raw.get("drainage_class"), 2, 5)
    return clamp(100 * (0.4 * elev + 0.3 * sun + 0.3 * drain))


@register("mushroom")
def _mushroom(raw: dict, cfg: dict) -> float:
    # Cultivated oyster/shiitake: cool, shaded, accessible; residue feedstock.
    cool = 1.0 - ramp(raw.get("summer_air_temp_c", 22), 18, 28)
    shade = ramp(raw.get("shade_fraction", 0.4), 0.2, 0.8)
    access = 1.0 - ramp(raw.get("market_access_km"), 5, 40)
    return clamp(100 * (0.4 * cool + 0.3 * shade + 0.3 * access))


# ── Water: springs ───────────────────────────────────────────────────────────
@register("spring_discharge")
def _spring_discharge(raw: dict, cfg: dict) -> float:
    if not raw.get("spring_present"):
        return 0.0
    base = clamp(raw.get("spring_discharge_cumec", 0) * cfg.get("cumec_scale", 25) * 100)
    decline = raw.get("spring_decline_fraction", 0.0)
    if decline >= cfg.get("collapse_threshold", 0.25):
        base *= 0.2  # imminent-collapse penalty (Aripal/Bulbul-style)
    return clamp(base)


@register("spring_wellness")
def _spring_wellness(raw: dict, cfg: dict) -> float:
    if not raw.get("spring_present"):
        return 0.0
    temp = raw.get("annual_water_temp_c", 12)
    warm = 20 if 19 <= temp <= 24 else (40 if temp >= 40 else 0)  # warm/geothermal bonus
    shrine = 30 * ramp(raw.get("shrine_proximity", 0.0), 0.0, 1.0)
    festival = 15 if raw.get("festival_site") else 0
    return clamp(15 + warm + shrine + festival)


@register("spring_resilience")
def _spring_resilience(raw: dict, cfg: dict) -> float:
    if not raw.get("spring_present"):
        return 0.0
    base = 65.0
    base -= 25 * raw.get("glacier_dependence", 0.3)
    base -= 30 * raw.get("spring_decline_fraction", 0.0)
    base += 10 * ramp(raw.get("spring_cluster_size", 1), 1, 8)  # redundancy
    base -= 20 * raw.get("mining_pressure", 0.0)
    return clamp(base)


# ── Energy / infrastructure ──────────────────────────────────────────────────
@register("hydropower")
def _hydropower(raw: dict, cfg: dict) -> float:
    # Run-of-river potential on larger streams (Indus Waters Treaty: physical only).
    head = ramp(raw.get("gross_head_m", 0), 10, 120)
    flow = ramp(raw.get("river_order", 0), 2, 6)
    return clamp(100 * (0.5 * head + 0.5 * flow))


@register("datacenter")
def _datacenter(raw: dict, cfg: dict) -> float:
    # Stream-cooled, hydro-powered AI DC: cool air, perennial water, grid/fiber,
    # gentle slope, away from floodplain/landslide.
    cool = 1.0 - ramp(raw.get("summer_air_temp_c", 22), 18, 30)
    water = 1.0 if raw.get("perennial_stream") or raw.get("near_water") else 0.3
    grid = ramp(raw.get("grid_proximity", 0.3), 0.2, 1.0)
    flat = 1.0 - ramp(raw.get("slope_deg"), 3, 20)
    hazard = 1.0 - 0.5 * raw.get("flood_fraction", 0.0) - 0.005 * raw.get("landslide", 0.0)
    return clamp(100 * (0.3 * cool + 0.25 * water + 0.2 * grid + 0.15 * flat) * max(0.2, hazard))


# ── Forest & rangeland ───────────────────────────────────────────────────────
@register("forest")
def _forest(raw: dict, cfg: dict) -> float:
    if raw.get("landcover") != "forest":
        return clamp(15 + 20 * ramp(raw.get("relief_m"), 100, 500))
    return clamp(60 + 40 * ramp(raw.get("shade_fraction", 0.5), 0.3, 0.9))


@register("ntfp_morel")
def _morel(raw: dict, cfg: dict) -> float:
    # Gucchi morel: coniferous/subalpine belt > 2000 m.
    belt = trapezoid(raw.get("elevation_m"), 1800, 2100, 3000, 3400)
    forest = 1.0 if raw.get("landcover") in {"forest", "meadow"} else 0.4
    return clamp(100 * (0.7 * belt + 0.3 * forest))


@register("fodder")
def _fodder(raw: dict, cfg: dict) -> float:
    # Green-fodder potential: cultivable/orchard land + water + season length.
    arable = 1.0 if raw.get("landcover") in {"cropland", "grassland", "meadow"} else 0.4
    water = 1.0 if raw.get("near_water") else 0.5
    season = ramp(raw.get("chilling_hours"), 1800, 600)  # lower elevation = longer season
    return clamp(100 * (0.45 * arable + 0.3 * water + 0.25 * (1 - ramp(raw.get("slope_deg"), 5, 30))) * (0.6 + 0.4 * season))


@register("agroforestry_fodder")
def _agroforestry(raw: dict, cfg: dict) -> float:
    # Silvi-pasture/intercrop: orchards, bunds, riverbanks, karewa.
    orchard = 1.0 if raw.get("orchard_present") else 0.0
    riparian = 1.0 if raw.get("near_water") else 0.0
    karewa = 1.0 if raw.get("soil_type") == "karewa" else 0.4
    slope_ok = 1.0 - ramp(raw.get("slope_deg"), 3, 18)
    return clamp(100 * (0.35 * orchard + 0.2 * riparian + 0.2 * karewa + 0.25 * slope_ok))


@register("transhumance_rangeland")
def _transhumance(raw: dict, cfg: dict) -> float:
    # Alpine/sub-alpine margs > ~2500 m.
    belt = trapezoid(raw.get("elevation_m"), 2300, 2600, 3600, 4200)
    meadow = 1.0 if raw.get("landcover") in {"meadow", "grassland"} else 0.3
    prod = ramp(raw.get("carrying_capacity_su"), 0, 6)
    return clamp(100 * (0.4 * belt + 0.3 * meadow + 0.3 * prod))


# ── Livestock ────────────────────────────────────────────────────────────────
@register("dairy")
def _dairy(raw: dict, cfg: dict) -> float:
    # Dairy suitability: fodder base + accessibility + valley-floor/mid land.
    fodder = _fodder(raw, {}) / 100
    access = 1.0 - ramp(raw.get("market_access_km"), 5, 40)
    elev = 1.0 - ramp(raw.get("elevation_m"), 2200, 3200)
    return clamp(100 * (0.5 * fodder + 0.3 * access + 0.2 * elev))


@register("sheep_mutton")
def _sheep(raw: dict, cfg: dict) -> float:
    graze = _grazing(raw, {"su_full": 6}) / 100
    range_belt = _transhumance(raw, {}) / 100
    return clamp(100 * (0.5 * graze + 0.5 * range_belt))


# ── Tourism niches ───────────────────────────────────────────────────────────
@register("tourism_border")
def _tourism_border(raw: dict, cfg: dict) -> float:
    # LoC border tourism: near the Line of Control, scenic, accessible in season.
    near_loc = 1.0 - ramp(raw.get("distance_to_loc_km", 80), 5, 60)
    scenery = ramp(raw.get("relief_m"), 100, 600)
    open_season = 1.0 - raw.get("pass_closure_fraction", 0.4)
    return clamp(100 * (0.5 * near_loc + 0.25 * scenery + 0.25 * open_season))


@register("tourism_astro")
def _tourism_astro(raw: dict, cfg: dict) -> float:
    # Dark-sky / astro: darkness (low Bortle), high+dry, accessible enough.
    dark = 1.0 - ramp(raw.get("bortle", 5), 1, 7)
    altitude = ramp(raw.get("elevation_m"), 2000, 4500)
    clear = 1.0 - raw.get("snow_cover_fraction", 0.3)
    return clamp(100 * (0.55 * dark + 0.3 * altitude + 0.15 * clear))


@register("tourism_wildlife")
def _tourism_wildlife(raw: dict, cfg: dict) -> float:
    # Snow-leopard HVLV: high-altitude rocky habitat.
    habitat = trapezoid(raw.get("elevation_m"), 3000, 3500, 5000, 5600)
    rugged = ramp(raw.get("slope_deg"), 15, 45)
    density = ramp(raw.get("snow_leopard_density", 0), 0.3, 3.0)
    return clamp(100 * (0.5 * habitat + 0.2 * rugged + 0.3 * density))


@register("tourism_trek")
def _tourism_trek(raw: dict, cfg: dict) -> float:
    # Winter frozen-river trek viability — collapses as winters warm.
    wt = raw.get("winter_mean_temp_c", -8)
    if wt >= -5:
        return clamp(10 * (1 - ramp(raw.get("relief_m"), 100, 500)))  # won't freeze
    freeze = trapezoid(wt, -25, -15, -10, -5)
    scenery = ramp(raw.get("relief_m"), 100, 700)
    return clamp(100 * (0.7 * freeze + 0.3 * scenery))


@register("tourism")
def _tourism_composite(raw: dict, cfg: dict) -> float:
    return clamp(
        max(
            _tourism(raw, {}),
            0.8 * _tourism_border(raw, {}),
            0.8 * _tourism_wildlife(raw, {}),
        )
    )


@register("minerals")
def _minerals(raw: dict, cfg: dict) -> float:
    base = {"limestone-shale": 80, "alluvium": 50, "karewa": 40}.get(raw.get("geology_unit", ""), 30)
    return clamp(base * (0.6 + 0.4 * (1 - ramp(raw.get("slope_deg"), 10, 40))))


@register("soil")
def _soil(raw: dict, cfg: dict) -> float:
    by_type = {"alluvial": 85, "sekil": 80, "karewa": 70, "dazanlad": 60, "nambal": 55, "mountain": 40}
    base = by_type.get(raw.get("soil_type", ""), 50)
    drain = ramp(raw.get("drainage_class"), 1, 5)
    return clamp(0.7 * base + 30 * drain)


@register("groundwater")
def _groundwater(raw: dict, cfg: dict) -> float:
    by_type = {"alluvial": 85, "karewa": 60, "sekil": 70, "dazanlad": 65, "nambal": 75, "mountain": 25}
    base = by_type.get(raw.get("soil_type", ""), 40)
    flat = 1.0 - ramp(raw.get("slope_deg"), 5, 30)
    return clamp(base * (0.6 + 0.4 * flat))


@register("biomass")
def _biomass(raw: dict, cfg: dict) -> float:
    residue = 1.0 if raw.get("landcover") in {"cropland", "forest"} else 0.3
    livestock = ramp(raw.get("carrying_capacity_su"), 0, 6)
    return clamp(100 * (0.6 * residue + 0.4 * livestock))


@register("landslide")
def _landslide(raw: dict, cfg: dict) -> float:
    # Higher = more susceptible (a hazard, not a benefit).
    return clamp(raw.get("landslide", 0.0))


def _generic(raw: dict, cfg: dict) -> float:
    """Fallback when a domain has no bespoke scorer yet: read a precomputed hint."""
    hint = raw.get("score_hint", {})
    return clamp(float(hint.get(cfg.get("_domain_id", ""), 0.0)))


# ── rubric loading + driving ─────────────────────────────────────────────────
def load_rubrics(rubric_dir: str | Path) -> dict[str, dict]:
    rubrics: dict[str, dict] = {}
    for path in sorted(Path(rubric_dir).glob("*.yaml")):
        rubrics[path.stem] = yaml.safe_load(path.read_text()) or {}
    return rubrics


def score_cell(raw: dict, domain_ids: list[str], rubrics: dict[str, dict]) -> dict[str, int]:
    """Compute every requested domain score for one cell's raw params."""
    out: dict[str, int] = {}
    for domain_id in domain_ids:
        cfg = dict(rubrics.get(domain_id, {}))
        cfg["_domain_id"] = domain_id
        scorer = _REGISTRY.get(domain_id, _generic)
        out[domain_id] = int(round(scorer(raw, cfg)))
    return out
