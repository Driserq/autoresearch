#!/usr/bin/env python3
"""runlog.py — capture autoresearch iteration records as JSONL, load them as a DataFrame.

Each iteration of a loop (or a data experiment) is one JSON object per line under
research/runs/<experiment>.jsonl. The write side is stdlib-only, so you can log runs
before the data stack is even installed; the read side (`load_runs`) needs pandas.

Conventional fields understood by analyze.py — all optional except experiment/iteration/score:
    experiment  str    experiment name / id (also the filename)
    iteration   int    iteration index (0, 1, 2, …)
    score       float  the mechanical metric value
    direction   str    'higher_is_better' (default) | 'lower_is_better'
    kept        bool   did the loop keep this candidate?
    tokens      int    tokens spent on this iteration
    seconds     float  wall-clock for this iteration
    note        str    free-form label

CLI:
    python research/lib/runlog.py append --experiment demo --iteration 0 --score 0.42 \
        --direction higher_is_better --tokens 5100 --kept true --note "baseline"
    python research/lib/runlog.py show   --experiment demo
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

RUNS_DIR = os.path.join(os.path.dirname(__file__), "..", "runs")


def _path(experiment: str, runs_dir: str = RUNS_DIR) -> str:
    return os.path.join(runs_dir, f"{experiment}.jsonl")


def append(record: dict, runs_dir: str = RUNS_DIR) -> str:
    """Append one iteration record. Returns the file path written to."""
    if "experiment" not in record:
        raise ValueError("record must include 'experiment'")
    record.setdefault("ts", datetime.now(timezone.utc).isoformat())
    record.setdefault("direction", "higher_is_better")
    os.makedirs(runs_dir, exist_ok=True)
    path = _path(record["experiment"], runs_dir)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def load_runs(experiment: str, runs_dir: str = RUNS_DIR):
    """Load an experiment's records into a pandas DataFrame (sorted by iteration)."""
    import pandas as pd  # lazy: only needed for analysis

    path = _path(experiment, runs_dir)
    if not os.path.exists(path):
        raise FileNotFoundError(f"no runs for '{experiment}' at {path}")
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    df = pd.DataFrame(rows)
    if "iteration" in df.columns:
        df = df.sort_values("iteration").reset_index(drop=True)
    return df


def _coerce(value: str):
    low = value.lower()
    if low in ("true", "false"):
        return low == "true"
    for cast in (int, float):
        try:
            return cast(value)
        except ValueError:
            continue
    return value


def main() -> None:
    ap = argparse.ArgumentParser(description="Append/inspect autoresearch run logs.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_app = sub.add_parser("append", help="append one iteration record")
    ap_app.add_argument("--experiment", required=True)
    ap_app.add_argument("--iteration", type=int, required=True)
    ap_app.add_argument("--score", type=float, required=True)
    ap_app.add_argument("--direction", choices=["higher_is_better", "lower_is_better"])
    ap_app.add_argument("--tokens", type=int)
    ap_app.add_argument("--seconds", type=float)
    ap_app.add_argument("--kept")
    ap_app.add_argument("--note")
    # Escape hatch for arbitrary extra fields: --set key=value (repeatable).
    ap_app.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")

    ap_show = sub.add_parser("show", help="print an experiment's records as a table")
    ap_show.add_argument("--experiment", required=True)

    args = ap.parse_args()

    if args.cmd == "append":
        rec = {"experiment": args.experiment, "iteration": args.iteration, "score": args.score}
        for k in ("direction", "tokens", "seconds", "note"):
            v = getattr(args, k)
            if v is not None:
                rec[k] = v
        if args.kept is not None:
            rec["kept"] = args.kept.lower() == "true"
        for pair in args.set:
            key, _, val = pair.partition("=")
            rec[key] = _coerce(val)
        print(append(rec))
    elif args.cmd == "show":
        print(load_runs(args.experiment).to_string(index=False))


if __name__ == "__main__":
    main()
