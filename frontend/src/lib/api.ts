const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface HexFeature {
  h3: string;
  scores: Record<string, number>;
}

export interface PlaceRef {
  place_id: number;
  name: string;
  overlap_fraction: number;
}

export interface CellProfile {
  h3_index: string;
  resolution: number;
  centroid: [number, number];
  elevation_m: number | null;
  confidence: number | null;
  scores: Record<string, number>;
  raw: Record<string, unknown>;
  places: PlaceRef[];
}

export interface PlaceSearchResult {
  place_id: number;
  name: string;
  kind: string;
  district: string | null;
}

export interface PlaceProfile {
  place_id: number;
  name: string;
  kind: string;
  district: string | null;
  population: number | null;
  cell_count: number;
  bbox: [number, number, number, number];
  scores: Record<string, number>;
  cell_ids: string[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${path}`);
  return (await res.json()) as T;
}

export const fetchHexes = (zoom: number, bbox?: string) =>
  get<{ resolution: number; count: number; hexes: HexFeature[] }>(
    `/api/hexes?zoom=${zoom}${bbox ? `&bbox=${bbox}` : ""}`,
  );

export const fetchCellById = (h3: string) => get<CellProfile>(`/api/cell/${h3}`);

export const fetchCellByPoint = (lat: number, lng: number) =>
  get<CellProfile>(`/api/cell?lat=${lat}&lng=${lng}`);

export const searchPlaces = (q: string) =>
  get<PlaceSearchResult[]>(`/api/places/search?q=${encodeURIComponent(q)}`);

export const fetchPlace = (id: number) => get<PlaceProfile>(`/api/place/${id}`);
