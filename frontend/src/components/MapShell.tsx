"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";

import { useAtlas } from "@/store/atlasStore";
import { fetchHexes } from "@/lib/api";
import DeckMapLibre from "@/components/DeckMapLibre";
import DomainSelector from "@/components/DomainSelector";
import Legend from "@/components/Legend";
import SearchBox from "@/components/SearchBox";
import ProfilePanel from "@/components/ProfilePanel";

// Cesium is heavy and browser-only: lazy-load it so 2.5D (the default) stays light.
const CesiumCanvas = dynamic(() => import("@/components/CesiumCanvas"), { ssr: false });

export default function MapShell() {
  const { mode, setMode, camera, setHexes, extrusion, toggleExtrusion } = useAtlas();

  // Load hexes for the current zoom. (Phase 0: small pilot, so a single fetch.)
  useEffect(() => {
    fetchHexes(camera.zoom)
      .then((r) => setHexes(r.hexes))
      .catch((e) => console.error("Failed to load hexes", e));
    // Re-fetch only when the resolution band changes, not on every pan.
  }, [Math.floor(camera.zoom), setHexes]);

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black text-white">
      {mode === "2d" ? <DeckMapLibre /> : <CesiumCanvas />}

      {/* Top-left controls */}
      <div className="absolute left-4 top-4 z-10 flex flex-col gap-3">
        <div className="rounded-lg bg-panel/90 p-1 backdrop-blur">
          <button
            onClick={() => setMode("2d")}
            className={`rounded px-3 py-1 text-sm ${mode === "2d" ? "bg-sky-600" : "bg-transparent"}`}
          >
            2.5D map
          </button>
          <button
            onClick={() => setMode("3d")}
            className={`rounded px-3 py-1 text-sm ${mode === "3d" ? "bg-sky-600" : "bg-transparent"}`}
          >
            3D globe
          </button>
        </div>
        <SearchBox />
        <DomainSelector />
        <label className="flex items-center gap-2 rounded-lg bg-panel/90 px-3 py-2 text-sm backdrop-blur">
          <input type="checkbox" checked={extrusion} onChange={toggleExtrusion} />
          Extrude by score
        </label>
      </div>

      <Legend />
      <ProfilePanel />
    </div>
  );
}
