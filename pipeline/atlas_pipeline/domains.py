"""Canonical capability-domain ids.

Mirror of packages/shared-types/domains.ts — keep the two in sync. These strings
are the keys written to grid_cell.scores and grid_cell.raw.

Only spatially-scoreable capabilities live here. Non-spatial economic/programmatic
data from the research foundation is captured in docs/DOMAIN_CATALOG.md.
"""

from __future__ import annotations

DOMAIN_IDS: list[str] = [
    # Agriculture & horticulture
    "agriculture",
    "apple",
    "saffron",
    "stonefruit",
    "paddy",
    "exotic_vegetables",
    "protected_cultivation",
    "berry",
    "indigenous_landrace",
    # Specialty / high-value crops
    "wasabi",
    "lavender",
    "culinary_herbs",
    "hops",
    "mushroom",
    "watercress",
    # Land & hazard
    "soil",
    "construction",
    "landslide",
    # Water
    "hydro_micro",
    "groundwater",
    "aquaculture_trout",
    "spring_discharge",
    "spring_wellness",
    "spring_resilience",
    # Energy & infrastructure
    "solar_pv",
    "biomass",
    "hydropower",
    "datacenter",
    # Forest & rangeland
    "forest",
    "grazing",
    "ntfp_morel",
    "fodder",
    "agroforestry_fodder",
    "transhumance_rangeland",
    # Livestock
    "dairy",
    "sheep_mutton",
    # Tourism
    "tourism",
    "tourism_border",
    "tourism_astro",
    "tourism_wildlife",
    "tourism_trek",
    # Human use
    "minerals",
]


def score_band(score: float) -> int:
    """0–100 -> 1–5 capability band (research-doc convention)."""
    if score <= 20:
        return 1
    if score <= 40:
        return 2
    if score <= 60:
        return 3
    if score <= 80:
        return 4
    return 5
