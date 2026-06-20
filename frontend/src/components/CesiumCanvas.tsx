"use client";

import { useEffect, useRef } from "react";
import * as Cesium from "cesium";
import { cellToBoundary } from "h3-js";
import "cesium/Build/Cesium/Widgets/widgets.css";

import { useAtlas } from "@/store/atlasStore";
import { DOMAIN_BY_ID } from "@kashmiratlas/shared-types";
import { scoreToRGBA, type RampId } from "@/lib/colorRamp";
import { zoomToHeight, heightToZoom } from "@/lib/camera";
import { fetchCellById } from "@/lib/api";

const ION_TOKEN = process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN ?? "";
const EXTRUSION_SCALE = 30; // metres per score-point — matches the deck.gl layer

/**
 * 3D mode: a Cesium globe with world terrain, rendering the SAME hex data and the
 * SAME score→colour logic as the 2.5D deck.gl mode (the documented hybrid fallback
 * that avoids depending on @deck.gl/cesium). Hexagons drape on real terrain and are
 * extruded by the selected domain score.
 */
export default function CesiumCanvas() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);
  const { camera, setCamera, setSelectedCell } = useAtlas();

  // Initialise the viewer once.
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;
    if (ION_TOKEN) Cesium.Ion.defaultAccessToken = ION_TOKEN;

    const viewer = new Cesium.Viewer(containerRef.current, {
      animation: false,
      timeline: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      fullscreenButton: false,
    });
    viewer.scene.globe.depthTestAgainstTerrain = true;
    viewerRef.current = viewer;

    // Use Cesium World Terrain when an ion token is present; flat ellipsoid otherwise.
    if (ION_TOKEN) {
      Cesium.createWorldTerrainAsync()
        .then((t) => (viewer.terrainProvider = t))
        .catch(() => undefined);
    }

    viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(
        camera.lng,
        camera.lat,
        zoomToHeight(camera.zoom, camera.lat),
      ),
      orientation: {
        heading: Cesium.Math.toRadians(camera.bearing),
        pitch: Cesium.Math.toRadians(-90 + camera.pitch),
        roll: 0,
      },
    });

    // Push camera changes back to the shared store (debounced via moveEnd).
    viewer.camera.moveEnd.addEventListener(() => {
      const carto = viewer.camera.positionCartographic;
      setCamera({
        lng: Cesium.Math.toDegrees(carto.longitude),
        lat: Cesium.Math.toDegrees(carto.latitude),
        zoom: heightToZoom(carto.height, Cesium.Math.toDegrees(carto.latitude)),
        pitch: 90 + Cesium.Math.toDegrees(viewer.camera.pitch),
        bearing: Cesium.Math.toDegrees(viewer.camera.heading),
      });
    });

    // Click → select cell.
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction(async (click: Cesium.ScreenSpaceEventHandler.PositionedEvent) => {
      const picked = viewer.scene.pick(click.position);
      const h3 = picked?.id?.properties?.h3?.getValue?.();
      if (h3) setSelectedCell(await fetchCellById(h3));
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    return () => {
      handler.destroy();
      viewer.destroy();
      viewerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Rebuild hex entities whenever data / domain / extrusion changes.
  const { hexes, selectedDomain, extrusion, highlightCellIds } = useAtlas();
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    const ramp = (DOMAIN_BY_ID[selectedDomain]?.ramp ?? "viridis") as RampId;

    viewer.entities.suspendEvents();
    viewer.entities.removeAll();
    for (const hex of hexes) {
      const score = hex.scores[selectedDomain];
      const [r, g, b, a] = scoreToRGBA(score, ramp);
      const boundary = cellToBoundary(hex.h3, true); // [lng, lat] pairs
      const positions = boundary.flatMap(([lng, lat]) => [lng, lat]);
      const highlighted = highlightCellIds.has(hex.h3);

      viewer.entities.add({
        properties: { h3: hex.h3 },
        polygon: {
          hierarchy: Cesium.Cartesian3.fromDegreesArray(positions),
          material: Cesium.Color.fromBytes(r, g, b, a),
          height: 0,
          extrudedHeight: extrusion ? (score ?? 0) * EXTRUSION_SCALE : undefined,
          outline: highlighted,
          outlineColor: Cesium.Color.WHITE,
        },
      });
    }
    viewer.entities.resumeEvents();
  }, [hexes, selectedDomain, extrusion, highlightCellIds]);

  return <div ref={containerRef} className="absolute inset-0" />;
}
