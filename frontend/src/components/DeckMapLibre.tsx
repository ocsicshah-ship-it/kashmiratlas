"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import "maplibre-gl/dist/maplibre-gl.css";

import { useAtlas } from "@/store/atlasStore";
import { buildHexLayer } from "@/components/layers/hexLayer";
import { fetchCellById } from "@/lib/api";

const MAPTILER_KEY = process.env.NEXT_PUBLIC_MAPTILER_KEY ?? "";
// MapTiler "outdoor" reads as a terrain-style basemap; falls back to a free demo style.
const STYLE = MAPTILER_KEY
  ? `https://api.maptiler.com/maps/outdoor-v2/style.json?key=${MAPTILER_KEY}`
  : "https://demotiles.maplibre.org/style.json";

/** 2.5D mode: deck.gl H3 hexagons interleaved over a MapLibre basemap. */
export default function DeckMapLibre() {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const { camera, setCamera, setSelectedCell } = useAtlas();

  // Initialise the map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE,
      center: [camera.lng, camera.lat],
      zoom: camera.zoom,
      pitch: camera.pitch,
      bearing: camera.bearing,
      maxPitch: 85,
    });
    const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
    map.addControl(overlay);
    mapRef.current = map;
    overlayRef.current = overlay;

    map.on("moveend", () => {
      const c = map.getCenter();
      setCamera({
        lng: c.lng,
        lat: c.lat,
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing(),
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
      overlayRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-apply camera when this mode mounts (e.g. after a switch from 3D).
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.jumpTo({
      center: [camera.lng, camera.lat],
      zoom: camera.zoom,
      pitch: camera.pitch,
      bearing: camera.bearing,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Rebuild the deck layer whenever the relevant store slices change.
  const { hexes, selectedDomain, extrusion, highlightCellIds } = useAtlas();
  useEffect(() => {
    overlayRef.current?.setProps({
      layers: [
        buildHexLayer({
          hexes,
          selectedDomain,
          extrusion,
          highlight: highlightCellIds,
          onClickHex: async (h3) => setSelectedCell(await fetchCellById(h3)),
        }),
      ],
    });
  }, [hexes, selectedDomain, extrusion, highlightCellIds, setSelectedCell]);

  return <div ref={containerRef} className="absolute inset-0" />;
}
