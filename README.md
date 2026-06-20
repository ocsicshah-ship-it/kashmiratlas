# Kashmir Valley Capability Atlas

A two-layer geospatial capability atlas for the Kashmir Valley, visualized in a **hybrid
"Google Earth / map style"** — fast 2.5D extruded H3 hexagons over a flat map **and** a true
3D-globe/terrain mode where hexagons drape on real mountains.

- **Layer 1** — an Uber **H3 resolution-9** hexagonal grid, each cell carrying capability scores
  (0–100) across ~12 domains (agriculture/apple/saffron, soil, geology/seismic, hydrology,
  energy/solar/micro-hydro, forestry, grazing, aquaculture/trout, foraging/NTFP, climate,
  construction, tourism, minerals) plus the raw parameters behind them.
- **Layer 2** — named places (villages/tehsils) that **inherit** cell scores via a `place_cell`
  spatial-join junction table (`overlap_fraction`-weighted aggregation).

## Architecture

```
 Pipeline (Python)        API (FastAPI)            Frontend (Next.js + deck.gl)
 ────────────────         ─────────────            ───────────────────────────
 H3 cells + scoring  ───▶ PostGIS (+h3-pg)  ◀────  2.5D: deck.gl over MapLibre
 zonal raster stats       REST + Arrow             3D:   deck.gl over CesiumJS
                                                   (one shared H3HexagonLayer)
```

Three guiding decisions:

1. **No hexagon polygons are stored or served.** We serve compact `h3_index` + score arrays and
   reconstruct geometry client-side on the GPU via deck.gl `H3HexagonLayer`. No tile server needed.
2. **deck.gl is the single hex-rendering engine in both modes.** 2.5D = deck.gl over MapLibre;
   3D = the *same* deck.gl layer driven by a Cesium camera. One layer factory, one data array.
3. **Phase 0 ships synthetic-but-realistic scores** for the Budgam/Doodhpathri–Yusmarg pilot tile so
   the full vertical slice works before any raster ingestion exists.

## Repository layout

```
kashmiratlas/
├─ docker-compose.yml        # postgis (+h3-pg) + api
├─ .env.example              # MAPTILER_KEY, CESIUM_ION_TOKEN, DATABASE_URL
├─ db/                       # Dockerfile (h3-pg) + migrations + seed
├─ pipeline/                 # Python H3 pipeline (cells, zonal, scoring, load, synthetic)
├─ api/                      # FastAPI REST service
├─ frontend/                 # Next.js + deck.gl + MapLibre + Cesium
├─ packages/shared-types/    # shared domain ids / score keys
└─ sample-data/              # pilot AOI + place boundaries
```

## Quick start (Phase 0)

```bash
cp .env.example .env          # fill in MAPTILER_KEY and CESIUM_ION_TOKEN (free tiers)

# 1. Database + API
docker compose up -d postgis
docker compose up -d api      # waits for postgis, runs migrations on first boot

# 2. Build the pilot grid with synthetic scores
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -e .
atlas-pipeline build --aoi ../sample-data/budgam_pilot.geojson --res 9 --synthetic

# 3. Frontend
cd ../frontend
npm install
npm run dev                   # http://localhost:3000
```

See [`docs/PHASING.md`](docs/PHASING.md) for the rollout plan and data-source provenance.

## License

Internal project — not yet licensed for redistribution.
