// Canonical capability-domain definitions shared by the frontend.
// The Python pipeline mirrors this list in pipeline/atlas_pipeline/domains.py.
// Keep the two in sync — the `id` strings are the keys used in grid_cell.scores.
//
// Domains here are the *spatially scoreable* capabilities (they vary per H3 cell).
// Non-spatial economic / programmatic data from the research foundation (HADP
// execution depth, FPO coverage, dairy formalization, poultry self-sufficiency,
// import-substitution trajectories, etc.) is captured in docs/DOMAIN_CATALOG.md
// rather than as per-cell scores.

export interface DomainDef {
  /** Stable key used in grid_cell.scores JSONB and API payloads. */
  id: string;
  /** Human-readable label for the domain selector and legend. */
  label: string;
  /** Grouping for the selector UI. */
  group: string;
  /** Default color ramp id (see frontend/src/lib/colorRamp.ts). */
  ramp: "viridis" | "magma" | "rdylgn" | "blues";
}

export const DOMAINS: DomainDef[] = [
  // ── Agriculture & horticulture ──────────────────────────────────────────
  { id: "agriculture", label: "Agriculture (composite)", group: "Agriculture", ramp: "rdylgn" },
  { id: "apple", label: "Apple", group: "Agriculture", ramp: "rdylgn" },
  { id: "saffron", label: "Saffron", group: "Agriculture", ramp: "rdylgn" },
  { id: "stonefruit", label: "Stone fruit / walnut", group: "Agriculture", ramp: "rdylgn" },
  { id: "paddy", label: "Paddy / rice", group: "Agriculture", ramp: "rdylgn" },
  { id: "exotic_vegetables", label: "Exotic vegetables", group: "Agriculture", ramp: "rdylgn" },
  { id: "protected_cultivation", label: "Protected cultivation (polyhouse)", group: "Agriculture", ramp: "rdylgn" },
  { id: "berry", label: "Berries (strawberry/blueberry)", group: "Agriculture", ramp: "rdylgn" },
  { id: "indigenous_landrace", label: "Indigenous landraces (haakh/nadru)", group: "Agriculture", ramp: "rdylgn" },

  // ── Specialty / high-value crops ────────────────────────────────────────
  { id: "wasabi", label: "Wasabi (sawa)", group: "Specialty", ramp: "blues" },
  { id: "lavender", label: "Lavender / aromatics", group: "Specialty", ramp: "magma" },
  { id: "culinary_herbs", label: "Culinary herbs", group: "Specialty", ramp: "viridis" },
  { id: "hops", label: "Hops", group: "Specialty", ramp: "viridis" },
  { id: "mushroom", label: "Cultivated mushroom", group: "Specialty", ramp: "viridis" },
  { id: "watercress", label: "Watercress", group: "Specialty", ramp: "blues" },

  // ── Land & hazard ───────────────────────────────────────────────────────
  { id: "soil", label: "Soil quality", group: "Land", ramp: "viridis" },
  { id: "construction", label: "Construction suitability", group: "Land", ramp: "rdylgn" },
  { id: "landslide", label: "Landslide susceptibility", group: "Land", ramp: "magma" },

  // ── Water ───────────────────────────────────────────────────────────────
  { id: "hydro_micro", label: "Micro-hydro potential", group: "Water", ramp: "blues" },
  { id: "groundwater", label: "Groundwater potential", group: "Water", ramp: "blues" },
  { id: "aquaculture_trout", label: "Trout aquaculture", group: "Water", ramp: "blues" },
  { id: "spring_discharge", label: "Karst spring discharge", group: "Water", ramp: "blues" },
  { id: "spring_wellness", label: "Spring wellness / pilgrimage", group: "Water", ramp: "blues" },
  { id: "spring_resilience", label: "Spring climate resilience", group: "Water", ramp: "magma" },

  // ── Energy & infrastructure ─────────────────────────────────────────────
  { id: "solar_pv", label: "Solar PV", group: "Energy", ramp: "magma" },
  { id: "biomass", label: "Biomass / biogas", group: "Energy", ramp: "viridis" },
  { id: "hydropower", label: "Hydropower (run-of-river)", group: "Energy", ramp: "blues" },
  { id: "datacenter", label: "Stream-cooled data centre", group: "Energy", ramp: "blues" },

  // ── Forest & rangeland ──────────────────────────────────────────────────
  { id: "forest", label: "Forest value", group: "Forest & range", ramp: "viridis" },
  { id: "grazing", label: "Grazing capacity", group: "Forest & range", ramp: "viridis" },
  { id: "ntfp_morel", label: "Foraging / morel (NTFP)", group: "Forest & range", ramp: "viridis" },
  { id: "fodder", label: "Green fodder potential", group: "Forest & range", ramp: "viridis" },
  { id: "agroforestry_fodder", label: "Silvi-pasture / intercrop", group: "Forest & range", ramp: "viridis" },
  { id: "transhumance_rangeland", label: "Transhumance marg productivity", group: "Forest & range", ramp: "viridis" },

  // ── Livestock ───────────────────────────────────────────────────────────
  { id: "dairy", label: "Dairy suitability", group: "Livestock", ramp: "rdylgn" },
  { id: "sheep_mutton", label: "Sheep / mutton", group: "Livestock", ramp: "rdylgn" },

  // ── Tourism ─────────────────────────────────────────────────────────────
  { id: "tourism", label: "Tourism (composite)", group: "Tourism", ramp: "viridis" },
  { id: "tourism_border", label: "LoC border tourism", group: "Tourism", ramp: "viridis" },
  { id: "tourism_astro", label: "Astro / dark-sky tourism", group: "Tourism", ramp: "magma" },
  { id: "tourism_wildlife", label: "Wildlife (snow leopard) tourism", group: "Tourism", ramp: "viridis" },
  { id: "tourism_trek", label: "Winter trek viability", group: "Tourism", ramp: "blues" },

  // ── Human use ───────────────────────────────────────────────────────────
  { id: "minerals", label: "Mineral / quarry", group: "Human use", ramp: "magma" },
];

export const DOMAIN_IDS = DOMAINS.map((d) => d.id);
export type DomainId = (typeof DOMAINS)[number]["id"];

export const DOMAIN_BY_ID: Record<string, DomainDef> = Object.fromEntries(
  DOMAINS.map((d) => [d.id, d]),
);

export const DOMAIN_GROUPS: string[] = Array.from(new Set(DOMAINS.map((d) => d.group)));

/** 0–100 -> 1–5 capability band, per the research-doc scoring convention. */
export function scoreBand(score: number): 1 | 2 | 3 | 4 | 5 {
  if (score <= 20) return 1;
  if (score <= 40) return 2;
  if (score <= 60) return 3;
  if (score <= 80) return 4;
  return 5;
}

export const BAND_LABELS: Record<number, string> = {
  1: "Unsuitable",
  2: "Marginal",
  3: "Moderate",
  4: "Good",
  5: "Excellent",
};
