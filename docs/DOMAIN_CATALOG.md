# Kashmir Valley Capability Atlas — Domain Catalog

This catalog is the authoritative knowledge base behind the atlas. It records every
capability domain, the raw parameters and numeric thresholds that drive its 0–100
score, the Kashmir-specific anchors used for calibration, and the source documents.

It also captures **non-spatial** economic / programmatic data (HADP execution,
import-substitution trajectories, value-chain gaps) from the research foundation
that informs the atlas but does **not** vary per hexagon — these are recorded here as
context and, where appropriate, surfaced as place/district attributes rather than as
per-cell scores.

Scoring convention (all domains): **0–20 unsuitable · 21–40 marginal · 41–60 moderate
· 61–80 good · 81–100 excellent**.

---

## 1. Spatial capability domains (per H3 cell)

These are implemented as scorers in `pipeline/atlas_pipeline/scoring.py`, tuned by
`pipeline/rubrics/*.yaml`, and rendered per cell in the frontend.

### Agriculture & horticulture

| Domain | Key raw params | Scoring summary | Kashmir anchors |
|---|---|---|---|
| `agriculture` | composite | 0.4·apple + 0.3·paddy + 0.3·exotic-veg | — |
| `apple` | elevation, chilling h, slope, aspect | optimal 1,500–2,700 m, 1,000–1,500 chill h, S/SE ≤20° slope, loam pH 5.5–6.5 | Baramulla 4.94 lakh MT; valley 20.4 lakh MT 2024-25; HDP 40–60 MT/ha vs seedling 6–13 |
| `saffron` | karewa gate, elevation, drainage, slope | hard-gated on karewa; 1,585–1,700 m, pH 6.8–7.8, ≤5° | Pampore/Pulwama 74.6% of area; GI No. 635; crocin 250+ vs Iran |
| `stonefruit` | elevation, aspect | 1,500–2,500 m warm karewa/margins | cherry/peach/apricot/walnut/almond |
| `paddy` | slope, irrigation, soil | <1,700 m, flat, sekil/alluvial/dazanlad | valley-floor command |
| `exotic_vegetables` | slope, water, market access, elevation | gentle slope + water + access; broccoli/capsicum/lettuce | 467 ha (2021-22); broccoli ₹100–150/kg (8–15×); Budgam ODOP |
| `protected_cultivation` | slope, GHI, access | flat + sunny + accessible polyhouse siting | HADP Project 3 ₹420 cr; 332 hi-tech + 848 low-cost (Feb 2026) |
| `berry` | soil pH, elevation, drainage, karewa | acidic karewa (pH 4.5–5.5) favours blueberry | strawberry 86 ha (Gasoo); blueberry trials ICAR-CITH; India imports 20k MT |
| `indigenous_landrace` | wetland, peri-urban | nambal/lake floating beds + peri-urban rich soils | Haakh −70% 2023-24; Nadru Dal/Anchar 6,000+ families |

### Specialty / high-value crops

| Domain | Key raw params | Scoring summary | Kashmir anchors |
|---|---|---|---|
| `wasabi` | spring/stream water temp, stability, discharge, elevation, shade | gate: cold flowing water; optimum 10–15 °C, disqualify >20 °C; 1,876–2,266 m | Kokernag 9–14 °C (benchmark, existing trout hatchery); Verinag 4.55 m³/s scale-out; Achabal/Martand disqualified (sacred); Malaknag/Gujnag 19–22 °C disqualified |
| `lavender` | aspect, drainage, elevation, karewa | sunny well-drained benches | Aroma Mission III >1,200 ha, 2,500 farmers, 61 stills; ₹20k→₹2 lakh/acre; CSIR-IIIM Bonera |
| `culinary_herbs` | elevation, GHI, access | Mediterranean-climate match | basil/parsley/thyme/rosemary; hydro 3–5× field price |
| `hops` | elevation, aspect, drainage | ~34 °N latitude match, deep soil | historic 1880s J&K industry; craft-beer 12% CAGR; no SKUAST program (whitespace) |
| `mushroom` | summer air temp, shade, access | cool shaded cultivation (oyster/shiitake) | SKUAST-K MRC; oyster commercial; morel wild = `ntfp_morel` |
| `watercress` | spring/stream, summer temp, gradient | cold spring-fed flowing water | retail ₹4,000–7,500/kg; Kashmir streams ideal |

### Land & hazard

| Domain | Scoring summary | Anchors |
|---|---|---|
| `soil` | by soil class (alluvial/sekil best) × drainage | karewa/alluvial/sekil/dazanlad/nambal/mountain |
| `construction` | slope + floodplain + landslide penalties on **Seismic Zone V** baseline | IS 1893:2016 Zone V valley-wide |
| `landslide` | Newmark-style slope × hazard (higher = worse) | 30 m grid susceptibility |

### Water

| Domain | Scoring summary | Anchors |
|---|---|---|
| `hydro_micro` | est_power_kw from P=ρgQHη, normalised | calibrate to JKSPDC plants |
| `groundwater` | aquifer lithology × flatness | alluvium/karewa favourable |
| `aquaculture_trout` | perennial flow, summer temp ≤16 °C, gradient | 2,650 MT 2024-25; ~90% of India; Anantnag "Trout District" |
| `spring_discharge` | discharge (m³/s) × scale; collapse penalty ≥25% decline | Verinag 4.55, Kokernag 1.16, Achabal 0.67; ~9 m³/s super-springs; Aripal/Bulbul dry 2024-25 |
| `spring_wellness` | temp class + shrine proximity + festival | Kheer Bhawani; Chumathang 40–60 °C; Panzath 500 springs (Gaade Maar) |
| `spring_resilience` | recharge source, glacier dependence, decline, cluster redundancy, mining | +0.8 °C since 1980; 10–15% glacier retreat; Sukhnag NGT mining ban |

### Energy & infrastructure

| Domain | Scoring summary | Anchors |
|---|---|---|
| `solar_pv` | GHI × aspect × (1−snow) × slope | J&K GHI 4.8–6.43; Srinagar ~2,203 sun-h/yr |
| `biomass` | residue cover + livestock density | straw + prunings + dung |
| `hydropower` | head × river order (run-of-river; Indus Waters Treaty = physical only) | Jhelum basin 3,084 MW identified; score physical potential |
| `datacenter` | cool air + perennial water + grid/fiber + flat − hazard | 3,540 MW operational hydro (7× ag demand); stream-cooled AI DC feasibility |

### Forest & rangeland

| Domain | Scoring summary | Anchors |
|---|---|---|
| `forest` | forest cover × canopy / relief | FSI deodar 1,675 km², mixed coniferous 3,557 km² |
| `grazing` | carrying capacity (sheep-units/ha) | quadrat biomass × utilisation × season |
| `ntfp_morel` | conifer/subalpine belt >2,000 m | gucchi (Kangan/Kupwara) |
| `fodder` | arable/orchard land + water + season | 41% UT green-fodder deficit (49% Kashmir); 2.15 lakh ha orchard intercrop |
| `agroforestry_fodder` | orchards, bunds, riverbanks, karewa | willow B/C 2.68–2.71; 3.34 lakh ha horti-pastoral |
| `transhumance_rangeland` | alpine marg >2,500 m × meadow × productivity | 4,500 km² margs; 30 lakh small ruminants; Bakarwal/Gujjar |

### Livestock

| Domain | Scoring summary | Anchors |
|---|---|---|
| `dairy` | fodder base + access + low/mid elevation | 29.74 lakh MT milk; 507 g/day per-capita; 95% informal "Goer" |
| `sheep_mutton` | grazing + transhumance belt | 41% mutton deficit (₹1,000–1,400 cr imports); SKUAST gene-edited Merino +30% muscle |

### Tourism

| Domain | Scoring summary | Anchors |
|---|---|---|
| `tourism` | composite of scenic/border/wildlife | Gulmarg, Pahalgam, Doodhpathri |
| `tourism_border` | LoC proximity + scenery + open-season | Gurez 111K→54K; Razdan Pass 3,556 m; e-permit |
| `tourism_astro` | darkness (Bortle) + altitude + clear sky | Hanle HDSR Bortle 1, 1,073 km², 24 ambassadors |
| `tourism_wildlife` | high rocky habitat × snow-leopard density | Ladakh 477 of 718; Hemis/Nubra ~3/100 km²; HVLV $3.6–5.4 M |
| `tourism_trek` | **inverts** as winters warm — needs winter mean ≤−8.6 °C to freeze | Chadar: 2024 no freeze, 2025 584 trekkers, 2026 cancelled |

### Human use

| Domain | Scoring summary | Anchors |
|---|---|---|
| `minerals` | geology unit × workability | limestone 15% of India reserves (Khrew); gypsum Uri 40 km |

---

## 2. Non-spatial economic & programmatic data (context, not per-cell)

These metrics describe value chains, programs, and import-substitution at the
**UT / district / program** level — they do not vary per hexagon and are kept here as
context (surfaceable later as district attributes or dashboard panels).

### Government programs
- **HADP** — ₹5,013 cr, 29 projects / 75 sub-schemes, 5–7 yr to FY2027-28, 13 lakh
  target households; >92,000 productive units, 3.7 lakh registered farmers, ~₹350 cr
  revenue, ~1.9 cr person-days (Jan 2026). Approval→operational conversion ~25% (gap);
  49% report subsidy-disbursement delays. Polyhouse applications saturated 2 Sep 2024.
- **JKCIP** — ~$217 M / ₹1,800 cr, 90 blocks, 300,000 households to 2030; 52%
  climate-smart & market-led; 45 new + 56 strengthened FPOs.
- **National Saffron Mission** — ₹400.11 cr; 2,598/3,665 ha rejuvenated; IIKSTC Dussu
  (₹37.81 cr); bore-wells 8/124 functional (infra gap).

### Value-chain gaps (whitespace for intervention)
- **Cold chain:** 70 cold stores (mostly apple), 1 blast freezer, 5 IQF (apple),
  reefer vans ≈0; NH-44 closure 2025 stranded 22,000 MT (~₹1,500 cr).
- **FPOs:** only 7 empanelled CBBOs (among India's lowest); Dal Lake Nadru FPO,
  FPO Shejaar, Glacial Trout FPO (first trout FPO) are early models.
- **Seed:** vegetable seed largely imported (Holland/Spain); seed-potato zones
  Gurez/Machil; no UT seed company; SKUAST-K 0 pure-veg cultivar releases (2025).
- **Mutton:** 41% deficit; HADP 3.1 (₹329 cr) importing 2,700 elite Dorper/Texel etc.
- **Poultry:** egg 97% / meat 69% shortfall; local share 85%→20% post-2019 toll change;
  ₹1,273–2,000 cr/yr imports. (Administrative — not gridded.)
- **Trout:** 388→1,649 private units, 1→9 hatcheries, 0→6 feed mills, 2→46 RAS
  (2021→2024-25); K2 Khyber ₹56.33 cr RAS flagship (1,500 MT target); FCR 1.56 vs
  global 0.6–1.1; no branded smoked-trout processor (faere heritage).
- **Apple:** HDP 836→1,119 ha; CA storage 3.07 vs 5 lakh MT demand; post-harvest loss
  20–25%; PMFBY never underwritten; scab needs 8–12 sprays; no apple GI.

### Climate & hazard signals (modulate many domains)
- Rainfall deficit every year since 2020; Jan 2025 −91%; 2026 snow-cover −27.8% (20-yr low).
- Hailstorms 200+ events 2010–2023; May 2025 >90% loss in 9 villages; Apr 2025 80–85%
  apple blossom loss (Shopian/Kulgam).
- Glacier mass loss 70.32 Gt (Kashmir–Ladakh); Drang Drung −13.84% (1971–2017).
- Seismic Zone V valley-wide (IS 1893:2016, current); IS 1893:2025 Zone VI withdrawn.

### Ladakh-specific (apply when the grid tiles beyond the Kashmir Valley)
- Snow-leopard HVLV tourism (Hemis NP 4,400 km², Ulley); Hanle dark-sky reserve;
  Zanskar Chadar collapse; geothermal springs (Chumathang/Puga/Panamik 40–110 °C);
  data-centre hydro base (Pakal Dul, Kiru, Kwar, Ratle under construction).

---

## 3. Sources

Primary research foundation + eight supplementary research documents (2025–2026):
H3 Grid Architecture & Data Stack; Tourism Niches & Yield-Collapse Risk; Springs &
Spring-Fed Water Sources; Wasabia japonica Engineering Blueprint; Livestock Feed &
Fodder Mission; and Research Reports 1–4 (vegetable economy; exotic crops / AI agronomy;
macro farming segments; stream-cooled data centres). Department datasets for production:
SKUAST-K, ICAR-NBSS&LUP, FSI, GSI, CGWB, IMD, JKSPDC, J&K Horticulture/Agriculture/
Animal Husbandry/Fisheries; CSIR-IIIM (Aroma Mission); HADP/JKCIP; Census village data.
