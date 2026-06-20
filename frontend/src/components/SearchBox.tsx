"use client";

import { useState } from "react";
import { searchPlaces, fetchPlace, type PlaceSearchResult } from "@/lib/api";
import { useAtlas } from "@/store/atlasStore";

export default function SearchBox() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<PlaceSearchResult[]>([]);
  const { setHighlight, setSelectedPlace, setSelectedCell, setCamera } = useAtlas();

  async function onChange(value: string) {
    setQ(value);
    if (value.trim().length < 2) {
      setResults([]);
      return;
    }
    try {
      setResults(await searchPlaces(value.trim()));
    } catch {
      setResults([]);
    }
  }

  async function select(r: PlaceSearchResult) {
    setQ(r.name);
    setResults([]);
    const place = await fetchPlace(r.place_id);
    setSelectedPlace(place);
    setSelectedCell(null);
    setHighlight(place.cell_ids);
    const [minLng, minLat, maxLng, maxLat] = place.bbox;
    setCamera({ lng: (minLng + maxLng) / 2, lat: (minLat + maxLat) / 2, zoom: 13 });
  }

  return (
    <div className="relative rounded-lg bg-panel/90 p-2 backdrop-blur">
      <input
        value={q}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search a village / tehsil…"
        className="w-64 rounded bg-panelMuted px-2 py-1 text-sm outline-none"
      />
      {results.length > 0 && (
        <ul className="absolute left-2 right-2 z-20 mt-1 max-h-64 overflow-auto rounded bg-panelMuted text-sm shadow-lg">
          {results.map((r) => (
            <li key={r.place_id}>
              <button
                onClick={() => select(r)}
                className="block w-full px-2 py-1 text-left hover:bg-sky-700"
              >
                {r.name}
                <span className="ml-2 text-xs text-slate-400">
                  {r.kind}
                  {r.district ? ` · ${r.district}` : ""}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
