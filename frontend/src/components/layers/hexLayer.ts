import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { DOMAIN_BY_ID } from "@kashmiratlas/shared-types";
import type { HexFeature } from "@/lib/api";
import { scoreToRGBA, type RampId } from "@/lib/colorRamp";

export interface HexLayerParams {
  hexes: HexFeature[];
  selectedDomain: string;
  extrusion: boolean;
  highlight: Set<string>;
  onClickHex: (h3: string) => void;
}

const EXTRUSION_SCALE = 30; // metres per score-point when extruded

/**
 * THE single source of truth for hex rendering. Used identically by the MapLibre
 * (2.5D) and Cesium (3D) modes — same data, same color/elevation accessors — so
 * switching modes never re-derives geometry or coloring.
 */
export function buildHexLayer(params: HexLayerParams): H3HexagonLayer<HexFeature> {
  const { hexes, selectedDomain, extrusion, highlight, onClickHex } = params;
  const ramp = (DOMAIN_BY_ID[selectedDomain]?.ramp ?? "viridis") as RampId;

  return new H3HexagonLayer<HexFeature>({
    id: "capability-hexes",
    data: hexes,
    pickable: true,
    wireframe: false,
    filled: true,
    extruded: extrusion,
    elevationScale: 1,
    getHexagon: (d) => d.h3,
    getFillColor: (d) => scoreToRGBA(d.scores[selectedDomain], ramp),
    getElevation: (d) => (extrusion ? (d.scores[selectedDomain] ?? 0) * EXTRUSION_SCALE : 0),
    getLineColor: (d) => (highlight.has(d.h3) ? [255, 255, 255, 255] : [255, 255, 255, 30]),
    getLineWidth: (d) => (highlight.has(d.h3) ? 4 : 1),
    lineWidthUnits: "pixels",
    stroked: true,
    onClick: (info) => {
      if (info.object) onClickHex(info.object.h3);
    },
    updateTriggers: {
      getFillColor: [selectedDomain],
      getElevation: [selectedDomain, extrusion],
      getLineColor: [highlight],
      getLineWidth: [highlight],
    },
  });
}
