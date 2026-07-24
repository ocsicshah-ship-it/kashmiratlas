import type { CameraState } from "@/store/atlasStore";

// Web-mercator zoom <-> camera altitude conversion so the MapLibre and Cesium
// cameras stay in sync across a mode switch. 512px tile, lat-corrected.
const TILE = 512;
const EARTH_CIRCUMFERENCE = 40075016.686; // metres

/** Metres-per-pixel at a given zoom + latitude. */
function metersPerPixel(zoom: number, lat: number): number {
  return (EARTH_CIRCUMFERENCE * Math.cos((lat * Math.PI) / 180)) / (TILE * 2 ** zoom);
}

/** Approximate Cesium camera height (m) that frames the same ground area as a MapLibre zoom. */
export function zoomToHeight(zoom: number, lat: number, viewportPx = 1000): number {
  const groundWidth = metersPerPixel(zoom, lat) * viewportPx;
  // height ~ groundWidth / (2 tan(fov/2)); Cesium default fov ~60deg.
  return groundWidth / (2 * Math.tan((60 * Math.PI) / 360));
}

/** Inverse: derive an equivalent MapLibre zoom from a Cesium camera height. */
export function heightToZoom(height: number, lat: number, viewportPx = 1000): number {
  const groundWidth = height * 2 * Math.tan((60 * Math.PI) / 360);
  const mpp = groundWidth / viewportPx;
  return Math.log2((EARTH_CIRCUMFERENCE * Math.cos((lat * Math.PI) / 180)) / (TILE * mpp));
}

export const cameraEquals = (a: CameraState, b: CameraState): boolean =>
  a.lng === b.lng && a.lat === b.lat && a.zoom === b.zoom && a.pitch === b.pitch && a.bearing === b.bearing;
