#!/usr/bin/env python3
"""Experiment skeleton: compute ONE mechanical metric and print `SCORE: <n>`.

This is the `Verify:` contract the autoresearch loop keys on — stdout must contain
a line `SCORE: <number>` and the process must exit 0 on success. Everything else
(how you compute the number) is yours to fill in.

Run:  .venv/bin/python research/experiments/_template/run.py
"""
from __future__ import annotations

import sys

import duckdb  # SQL over CSV/Parquet/JSON with no server


def compute_score() -> float:
    # --- replace this block with your real metric --------------------------
    # Example: DuckDB reads a file and returns an aggregate. Swap in your data
    # source (a results.csv the loop produced, a Parquet export, PostHog dump…).
    #
    #   rel = duckdb.sql("SELECT avg(latency_ms) AS m FROM 'research/data/runs.csv'")
    #   return float(rel.fetchone()[0])
    #
    # Demo stand-in so the template runs out of the box:
    rel = duckdb.sql("SELECT count(*) FILTER (WHERE x > 0.5) / count(*) FROM range(100) t(x)")
    _ = rel  # (illustrative; the line below is the actual demo value)
    return float(duckdb.sql("SELECT 0.5").fetchone()[0])
    # -----------------------------------------------------------------------


def main() -> int:
    try:
        score = compute_score()
    except Exception as exc:  # verify failed → non-zero exit, no SCORE line
        print(f"verify error: {exc}", file=sys.stderr)
        return 1
    print(f"SCORE: {score}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
