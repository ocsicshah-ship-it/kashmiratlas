"""Kashmir Valley Capability Atlas — data pipeline.

Generates the H3 res-9 grid for an area of interest, aggregates source rasters
to cells (Phase 1+), computes capability scores via a pluggable rubric registry,
and loads everything into PostGIS.
"""

__version__ = "0.1.0"
