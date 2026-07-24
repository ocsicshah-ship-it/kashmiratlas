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

## Phase 1 — real data on the pilot (in progress)
- **Terrain — done.** `--dem <GeoTIFF>` zonal-aggregates a real DEM (Copernicus GLO-30 tested)
  to per-cell elevation + slope + aspect (`zonal.terrain_from_dem`); slope is computed in metres
  even for geographic DEMs. Lifts `confidence` to 55.
- **Land cover — done.** `--landcover <GeoTIFF>` takes the modal ESA WorldCover class per cell
  (`zonal.modal_landcover`) → real forest/grassland/cropland/meadow/built/… driving the forest,
  grazing, agriculture, fodder and NTFP scores. `/api/hexes` also serves Arrow IPC.
- **Remaining.** Solar (Global Solar Atlas GHI), soil (NBSS/SKUAST), lapse-rate climate surfaces,
  then replace the remaining synthetic params; calibrate rubrics against ground truth.

Fetch the pilot source rasters (no auth) and ingest:
```
curl -L -o data/dem_n33_e074.tif \
  https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N33_00_E074_00_DEM/Copernicus_DSM_COG_10_N33_00_E074_00_DEM.tif
curl -L -o data/worldcover_N33E072.tif \
  https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N33E072_Map.tif
atlas-pipeline build --aoi sample-data/budgam_pilot.geojson --res 9 \
  --dem data/dem_n33_e074.tif --landcover data/worldcover_N33E072.tif
```

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
