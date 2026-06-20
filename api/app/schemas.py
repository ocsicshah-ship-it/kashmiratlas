"""Pydantic response models."""

from __future__ import annotations

from pydantic import BaseModel


class PlaceRef(BaseModel):
    place_id: int
    name: str
    overlap_fraction: float


class CellProfile(BaseModel):
    h3_index: str
    resolution: int
    centroid: list[float]  # [lng, lat]
    elevation_m: float | None = None
    confidence: int | None = None
    scores: dict[str, int]
    raw: dict
    places: list[PlaceRef] = []


class PlaceSearchResult(BaseModel):
    place_id: int
    name: str
    kind: str
    district: str | None = None


class PlaceProfile(BaseModel):
    place_id: int
    name: str
    kind: str
    district: str | None = None
    population: int | None = None
    cell_count: int
    bbox: list[float]  # [minLng, minLat, maxLng, maxLat]
    scores: dict[str, int]  # overlap-weighted mean per domain
    cell_ids: list[str]


class HexFeature(BaseModel):
    h3: str
    scores: dict[str, int]


class HexCollection(BaseModel):
    resolution: int
    count: int
    hexes: list[HexFeature]
