"""Database helpers for the pipeline (psycopg 3)."""

from __future__ import annotations

import os

import psycopg


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and export it, e.g.\n"
            "  export DATABASE_URL=postgresql://atlas:atlas@localhost:5432/kashmiratlas"
        )
    return url


def connect() -> psycopg.Connection:
    """Open an autocommit=False connection; callers manage transactions."""
    return psycopg.connect(database_url())
