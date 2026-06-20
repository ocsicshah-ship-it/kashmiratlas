// Copies Cesium's static runtime assets into public/cesium so the 3D mode can
// load Workers/Assets/Widgets at runtime (referenced via CESIUM_BASE_URL=/cesium).
import { cp, mkdir, access } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "..", "node_modules", "cesium", "Build", "Cesium");
const dest = join(here, "..", "public", "cesium");

try {
  await access(src);
} catch {
  console.warn("[copy-cesium] cesium build not found yet; skipping (run after install).");
  process.exit(0);
}

await mkdir(dest, { recursive: true });
for (const dir of ["Workers", "Assets", "Widgets", "ThirdParty"]) {
  await cp(join(src, dir), join(dest, dir), { recursive: true }).catch(() => {});
}
console.log("[copy-cesium] copied Cesium static assets to public/cesium");
