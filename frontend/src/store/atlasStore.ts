import { create } from "zustand";
import { DOMAINS } from "@kashmiratlas/shared-types";
import type { HexFeature, CellProfile, PlaceProfile } from "@/lib/api";

export type MapMode = "2d" | "3d";

/** Mode-agnostic camera so 2.5D (MapLibre) and 3D (Cesium) can share view state. */
export interface CameraState {
  lng: number;
  lat: number;
  zoom: number;
  pitch: number;
  bearing: number;
}

interface AtlasState {
  mode: MapMode;
  selectedDomain: string;
  extrusion: boolean;
  camera: CameraState;

  hexes: HexFeature[];
  highlightCellIds: Set<string>;

  selectedCell: CellProfile | null;
  selectedPlace: PlaceProfile | null;

  setMode: (m: MapMode) => void;
  setSelectedDomain: (d: string) => void;
  toggleExtrusion: () => void;
  setCamera: (c: Partial<CameraState>) => void;
  setHexes: (h: HexFeature[]) => void;
  setHighlight: (ids: string[]) => void;
  setSelectedCell: (c: CellProfile | null) => void;
  setSelectedPlace: (p: PlaceProfile | null) => void;
}

// Pilot corridor centroid (Budgam / Doodhpathri–Yusmarg).
const INITIAL_CAMERA: CameraState = {
  lng: 74.7,
  lat: 33.88,
  zoom: 12,
  pitch: 45,
  bearing: 0,
};

export const useAtlas = create<AtlasState>((set) => ({
  mode: "2d",
  selectedDomain: DOMAINS[0].id,
  extrusion: true,
  camera: INITIAL_CAMERA,

  hexes: [],
  highlightCellIds: new Set(),

  selectedCell: null,
  selectedPlace: null,

  setMode: (mode) => set({ mode }),
  setSelectedDomain: (selectedDomain) => set({ selectedDomain }),
  toggleExtrusion: () => set((s) => ({ extrusion: !s.extrusion })),
  setCamera: (c) => set((s) => ({ camera: { ...s.camera, ...c } })),
  setHexes: (hexes) => set({ hexes }),
  setHighlight: (ids) => set({ highlightCellIds: new Set(ids) }),
  setSelectedCell: (selectedCell) => set({ selectedCell }),
  setSelectedPlace: (selectedPlace) => set({ selectedPlace }),
}));
