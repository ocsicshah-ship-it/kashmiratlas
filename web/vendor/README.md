# Vendored third-party libraries

Bundled locally so the atlas page (`web/index.html`) has **no CDN dependency**
(works offline / behind firewalls, and is deterministically testable).

| File | Library | Version | License | Source |
|---|---|---|---|---|
| `h3-js.umd.js` | Uber H3 (JS) | 4.1.0 | Apache-2.0 | jsdelivr: `h3-js@4.1.0/dist/h3-js.umd.js` |
| `leaflet.js` | Leaflet | 1.9.4 | BSD-2-Clause | jsdelivr: `leaflet@1.9.4/dist/leaflet.js` |
| `leaflet.css` | Leaflet | 1.9.4 | BSD-2-Clause | jsdelivr: `leaflet@1.9.4/dist/leaflet.css` |

Basemap tiles and web fonts are still fetched from their providers at runtime
(cosmetic — the map and all scores work without them).
