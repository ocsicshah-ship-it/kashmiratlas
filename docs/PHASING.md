# Atlas build phasing

Mirrors the research foundation's phased plan. Phase 0 is implemented in this repo.

## Phase 0 — vertical slice on the Budgam pilot (implemented)
Stand up PostGIS + API + hybrid frontend end-to-end on the Budgam /
Mujhpathri–Doodhpathri–Yusmarg corridor (`sample-data/budgam_pilot.geojson`) with
**synthetic-but-realistic** scores so the hybrid map renders, colours by any domain,
extrudes by score, and is clickable (cell profile + village lookup) before any raster
ingestion exists.

- H3 res-9 polyfill of the pilot AOI (`pipeline cells.py`)
- Deterministic synthetic raw params → real scoring registry (`synthetic.py` + `scoring.py`)
- Load into PostGIS; spatial-join places; refresh res-7/res-8 roll-ups (`load.py`)
- API: `/api/cell`, `/api/cell/{id}`, `/api/places/search`, `/api/place/{id}`, `/api/hexes`
- Frontend: deck.gl `H3HexagonLayer` over MapLibre (2.5D) + native Cesium polygons (3D),
  one shared data array + colour logic, domain selector, legend, search, profile panel

## Phase 1 — real data on the pilot
Wire `zonal.py` to ALOS/SRTM DEM + ESA WorldCover + Global Solar Atlas for the pilot
AOI; replace synthetic scores with measured raw params; calibrate rubrics against ground
truth and department records; switch `/api/hexes` to Arrow IPC.

## Phase 2 — tile outward (valley-wide, ~150k res-9 cells)
South Kashmir (saffron + Lidder/Bringi trout), then North Kashmir (Wular/Hokersar,
gypsum/Uri, Sindh/Kishanganga hydro, high-altitude MAP/snow belts). Add zoom-based
res-7/res-8 serving + single cached Arrow blob + CDN.

## Phase 3 — Ladakh extension + polish
Add Ladakh tiles to activate snow-leopard/astro/Chadar/geothermal/data-centre domains;
self-hosted pmtiles basemap + self-hosted terrain; multi-domain comparison views; export.

## Phase 4 — living database
Annual refresh of land-cover/snow/climate; event-driven updates after floods/landslides;
versioned scores; department/community feedback loop.
