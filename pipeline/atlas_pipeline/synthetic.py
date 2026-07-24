"""Deterministic synthetic raw parameters for Phase 0.

Produces plausible terrain/soil/climate/water values per cell so the full stack
renders and is clickable before real raster ingestion exists. Values are a
deterministic function of the H3 index + centroid, so rebuilds are stable. The
synthetic ``raw`` dicts are fed through the *real* scoring registry, so every
domain's rubric gets exercised too.
"""

from __future__ import annotations

import hashlib
import math

from .cells import Cell

_SOILS = ["karewa", "alluvial", "sekil", "dazanlad", "nambal", "mountain"]
_LANDCOVER = ["forest", "grassland", "meadow", "cropland", "bare", "snow"]
_GEOLOGY = ["alluvium", "karewa", "granite", "limestone-shale", "slate-quartzite", "tuff"]


def _unit_hash(key: str, salt: str) -> float:
    """Stable pseudo-random float in [0, 1) from a string key."""
    digest = hashlib.sha256(f"{salt}:{key}".encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def synth_raw(cell: Cell, terrain: dict | None = None) -> dict:
    """Build a deterministic raw-parameter dict for one cell.

    If ``terrain`` is given (e.g. {'elevation_m','slope_deg','aspect_deg'} zonal-
    aggregated from a real DEM), those values are used verbatim and every
    elevation/slope-dependent field downstream is grounded in the real terrain;
    the remaining un-sourced fields stay deterministic-synthetic. If ``terrain``
    is None, a modelled elevation surface is used (Phase 0).
    """
    h = lambda s: _unit_hash(cell.h3_index, s)  # noqa: E731
    real = terrain or {}

    if real.get("elevation_m") is not None:
        elevation_m = round(float(real["elevation_m"]), 1)
    else:
        # Modelled: valley floor in the NE, rising toward the SW alpine meadows.
        base = 1600 + (33.98 - cell.lat) * 5200 + (74.84 - cell.lng) * 1500
        elevation_m = max(1550.0, min(3300.0, round(base + (h("elev") - 0.5) * 350, 1)))

    slope_deg = round(float(real["slope_deg"]), 1) if real.get("slope_deg") is not None else round(2 + h("slope") * 38, 1)
    aspect_deg = float(real["aspect_deg"]) if real.get("aspect_deg") is not None else h("aspect") * 360
    aspect_south_factor = round((1 + math.cos(math.radians(aspect_deg - 180))) / 2, 3)
    relief_m = round(20 + h("relief") * 600, 1)

    # Soil: karewa more likely at lower benches, mountain soils up high.
    soil = "karewa" if (elevation_m < 1750 and h("soil") > 0.5) else _SOILS[int(h("soil2") * len(_SOILS))]
    soil_ph = round(4.5 + h("ph") * 3.3, 2) if soil == "karewa" else round(5.8 + h("ph") * 2.0, 2)
    if real.get("landcover"):
        lc = real["landcover"]
        # a real DEM lets us refine WorldCover "grassland" up high into alpine meadow.
        landcover = "meadow" if (lc == "grassland" and elevation_m > 2500) else lc
    else:
        landcover = "meadow" if elevation_m > 2500 else _LANDCOVER[int(h("lc") * len(_LANDCOVER))]
    geology = _GEOLOGY[int(h("geo") * len(_GEOLOGY))]

    perennial = h("stream") > 0.6
    near_water = perennial or h("water") > 0.7
    spring_present = h("spring") > 0.82
    spring_discharge = round(h("spdis") * (5.0 if spring_present else 0.0), 3)
    summer_water_temp_c = round(10 + (elevation_m < 2200) * 8 + h("temp") * 6, 1)
    annual_water_temp_c = round(9 + h("atemp") * 13, 1)  # 9–22C; some warm karst
    summer_air_temp_c = round(30 - (elevation_m - 1600) / 120 + (h("airt") - 0.5) * 4, 1)
    winter_mean_temp_c = round(-2 - (elevation_m - 1600) / 180 - h("wtemp") * 6, 1)

    orchard_present = landcover == "cropland" and elevation_m < 2200 and h("orch") > 0.4
    market_access_km = round(2 + h("mkt") * 45, 1)

    return {
        # ── terrain ──
        "elevation_m": elevation_m,
        "slope_deg": slope_deg,
        "aspect_deg": round(aspect_deg, 1),
        "aspect_south_factor": aspect_south_factor,
        "relief_m": relief_m,
        # ── soil / geology / cover ──
        "soil_type": soil,
        "soil_ph": soil_ph,
        "drainage_class": int(1 + h("drain") * 4),
        "landcover": landcover,
        "geology_unit": geology,
        "orchard_present": orchard_present,
        "shade_fraction": round(0.7 * (landcover == "forest") + h("shade") * 0.3, 2),
        # ── climate / solar ──
        "ghi_kwh_m2_day": round(4.0 + aspect_south_factor * 1.6 - (elevation_m > 2600) * 0.4, 2),
        "snow_cover_fraction": round(min(0.9, max(0.05, (elevation_m - 1600) / 2000)), 2),
        "snow_cover_days": int(30 + (elevation_m - 1600) / 8),
        "chilling_hours": int(700 + (elevation_m - 1500) * 0.55),
        "summer_air_temp_c": summer_air_temp_c,
        "winter_mean_temp_c": winter_mean_temp_c,
        # ── water / hydro / springs ──
        "perennial_stream": perennial,
        "near_water": near_water,
        "stream_gradient": round(0.005 + slope_deg / 1000, 4),
        "est_power_kw": round(h("power") * 200 * (1.5 if perennial else 0.2), 1),
        "gross_head_m": round(slope_deg * 3 + h("head") * 60, 1),
        "river_order": int(h("river") * 6) if near_water else 0,
        "summer_water_temp_c": summer_water_temp_c,
        "annual_water_temp_c": annual_water_temp_c,
        "water_temp_stability": round(0.4 + h("stab") * 0.6, 2),
        "spring_present": spring_present,
        "spring_discharge_cumec": spring_discharge,
        "spring_decline_fraction": round(h("decl") * 0.5, 2) if spring_present else 0.0,
        "spring_cluster_size": int(1 + h("clus") * 8) if spring_present else 0,
        "glacier_dependence": round(min(0.9, (elevation_m - 1600) / 2200), 2),
        "shrine_proximity": round(h("shrine"), 2),
        "festival_site": h("fest") > 0.9,
        "mining_pressure": round(h("mine") * 0.6, 2),
        # ── range / hazard ──
        "carrying_capacity_su": round((landcover in {"meadow", "grassland"}) * h("graze") * 6, 2),
        "landslide": round(slope_deg * 1.8 + h("ls") * 25, 1),
        "flood_fraction": round(max(0.0, (1800 - elevation_m) / 1800) if elevation_m < 1800 else 0.0, 2),
        # ── infrastructure / access ──
        "market_access_km": market_access_km,
        "grid_proximity": round(1.0 - min(1.0, market_access_km / 50), 2),
        # ── tourism niches ──
        "distance_to_loc_km": round(max(0.0, (cell.lng - 74.3) * 70 + h("loc") * 20), 1),
        "pass_closure_fraction": round(min(0.8, (elevation_m - 2000) / 2500) if elevation_m > 2000 else 0.1, 2),
        "bortle": round(2 + (market_access_km < 10) * 3 + (3 - min(3, market_access_km / 15)), 1),
        "snow_leopard_density": round(h("sl") * 3 if elevation_m > 3000 else 0.0, 2),
        # ── meta ──
        # real DEM terrain lifts confidence; fully-synthetic stays low.
        "confidence": 55 if real.get("elevation_m") is not None else 35,
    }
