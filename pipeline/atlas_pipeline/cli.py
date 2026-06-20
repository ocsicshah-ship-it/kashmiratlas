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
        False, "--synthetic", help="Generate synthetic raw params instead of ingesting rasters."
    ),
    places: Path = typer.Option(
        _SEED_PLACES, "--places", help="GeoJSON of named places to load (Layer 2)."
    ),
) -> None:
    """Generate cells for the AOI, score them, and load everything into PostGIS."""
    console.print(f"[bold]Polyfilling[/] {aoi} at res {res} …")
    cell_list = cells_mod.cells_for_geojson(aoi, res)
    console.print(f"  → {len(cell_list):,} H3 cells")

    if not synthetic_mode:
        raise typer.BadParameter(
            "Only --synthetic is wired in Phase 0. Raster ingestion (zonal.py) lands in Phase 1."
        )

    console.print("Generating synthetic raw parameters …")
    raw_by_id = {c.h3_index: synthetic.synth_raw(c) for c in cell_list}

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
