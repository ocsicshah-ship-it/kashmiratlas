"""atlas-pipeline command-line interface."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from . import cells as cells_mod
from . import db, load, scoring, synthetic
from .domains import DOMAIN_IDS

app = typer.Typer(add_completion=False, help="Kashmir Valley Capability Atlas pipeline.")
console = Console()

_RUBRIC_DIR = Path(__file__).resolve().parent.parent / "rubrics"
_SEED_PLACES = Path(__file__).resolve().parents[2] / "db" / "seed" / "places.geojson"


@app.command()
def build(
    aoi: Path = typer.Option(..., "--aoi", help="GeoJSON area of interest to polyfill."),
    res: int = typer.Option(9, "--res", help="H3 resolution."),
    synthetic_mode: bool = typer.Option(
        False, "--synthetic", help="Generate synthetic raw params (Phase 0)."
    ),
    dem: Path = typer.Option(
        None, "--dem", help="DEM GeoTIFF: real terrain (elevation/slope/aspect) per cell (Phase 1)."
    ),
    landcover: Path = typer.Option(
        None, "--landcover", help="ESA WorldCover GeoTIFF: real modal land cover per cell (Phase 1)."
    ),
    places: Path = typer.Option(
        _SEED_PLACES, "--places", help="GeoJSON of named places to load (Layer 2)."
    ),
) -> None:
    """Generate cells for the AOI, score them, and load everything into PostGIS."""
    console.print(f"[bold]Polyfilling[/] {aoi} at res {res} …")
    cell_list = cells_mod.cells_for_geojson(aoi, res)
    console.print(f"  → {len(cell_list):,} H3 cells")

    if not synthetic_mode and dem is None and landcover is None:
        raise typer.BadParameter(
            "Pass --synthetic (Phase 0) and/or --dem / --landcover <GeoTIFF> (Phase 1)."
        )

    terrain: dict[str, dict] = {}
    if dem is not None:
        from . import zonal

        console.print(f"Aggregating real terrain from DEM [cyan]{dem}[/] …")
        work = Path(__file__).resolve().parents[1] / ".terrain_work"
        terrain = zonal.terrain_from_dem(cell_list, dem, work)
        console.print(f"  → real terrain for {len(terrain):,}/{len(cell_list):,} cells")
    if landcover is not None:
        from . import zonal

        console.print(f"Aggregating real land cover from [cyan]{landcover}[/] …")
        lc = zonal.modal_landcover(cell_list, landcover)
        for h3_index, cat in lc.items():
            terrain.setdefault(h3_index, {})["landcover"] = cat
        console.print(f"  → real land cover for {len(lc):,}/{len(cell_list):,} cells")

    console.print("Generating raw parameters …")
    raw_by_id = {c.h3_index: synthetic.synth_raw(c, terrain.get(c.h3_index)) for c in cell_list}

    console.print("Scoring cells …")
    rubrics = scoring.load_rubrics(_RUBRIC_DIR)
    scores_by_id = {
        h3_index: scoring.score_cell(raw, DOMAIN_IDS, rubrics)
        for h3_index, raw in raw_by_id.items()
    }

    console.print("Loading into PostGIS …")
    with db.connect() as conn:
        n_cells = load.upsert_cells(conn, cell_list, raw_by_id, scores_by_id)
        n_places = load.load_places(conn, places)
        n_join = load.rebuild_place_cell(conn, cell_list)
        load.refresh_rollups(conn)

    console.print(
        f"[green]Done.[/] {n_cells:,} cells, {n_places} places, "
        f"{n_join:,} place–cell links; roll-ups refreshed."
    )


@app.command()
def domains() -> None:
    """List the capability domains and which have a bespoke scorer."""
    registered = set(scoring.registered_domains())
    for d in DOMAIN_IDS:
        mark = "[green]✓ scorer[/]" if d in registered else "[yellow]generic[/]"
        console.print(f"  {d:20s} {mark}")


if __name__ == "__main__":
    app()
