#!/usr/bin/env python3
"""analyze.py — turn a run log into the numbers the autoresearch thesis cares about.

Given research/runs/<experiment>.jsonl (written by runlog.py), it computes:
    - best-so-far curve          (is the metric still climbing?)
    - plateau detection          (last N iterations flat within epsilon?)
    - cost efficiency            (total improvement per 1k tokens)
    - kept-rate                  (share of candidates the loop accepted)
and, if matplotlib is available, saves a score + best-so-far + cumulative-tokens plot.

Usage:
    python research/lib/analyze.py --experiment demo
    python research/lib/analyze.py --experiment demo --plateau-window 4 --out demo.png
"""
from __future__ import annotations

import argparse
import os

from runlog import load_runs  # same directory


def summarize(df, plateau_window: int = 4, epsilon: float = 1e-9) -> dict:
    direction = str(df.get("direction", ["higher_is_better"]).iloc[0]) if "direction" in df else "higher_is_better"
    higher = direction != "lower_is_better"
    scores = df["score"].astype(float)

    best_so_far = scores.cummax() if higher else scores.cummin()
    total_gain = float((best_so_far.iloc[-1] - best_so_far.iloc[0]) * (1 if higher else -1))

    # Plateau: no net improvement in best-so-far across the last `plateau_window` steps.
    window = best_so_far.tail(plateau_window)
    plateaued = len(window) >= plateau_window and abs(window.iloc[-1] - window.iloc[0]) <= epsilon

    tokens = float(df["tokens"].astype(float).sum()) if "tokens" in df else 0.0
    kept_rate = float(df["kept"].mean()) if "kept" in df else float("nan")
    per_1k = (total_gain / tokens * 1000.0) if tokens > 0 else float("nan")

    return {
        "experiment": str(df["experiment"].iloc[0]) if "experiment" in df else "?",
        "direction": direction,
        "iterations": int(len(df)),
        "start": float(scores.iloc[0]),
        "best": float(best_so_far.iloc[-1]),
        "total_gain": total_gain,
        "plateaued": bool(plateaued),
        "tokens_total": tokens,
        "gain_per_1k_tokens": per_1k,
        "kept_rate": kept_rate,
    }


def plot(df, out_path: str) -> str | None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    higher = str(df.get("direction", ["higher_is_better"]).iloc[0]) != "lower_is_better" if "direction" in df else True
    it = df["iteration"] if "iteration" in df else range(len(df))
    scores = df["score"].astype(float)
    best = scores.cummax() if higher else scores.cummin()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(it, scores, marker="o", label="score", color="#4C78A8")
    ax.plot(it, best, linestyle="--", label="best so far", color="#E45756")
    ax.set_xlabel("iteration")
    ax.set_ylabel("score")
    ax.set_title(f"{df['experiment'].iloc[0] if 'experiment' in df else 'experiment'} — convergence")
    ax.legend(loc="best")

    if "tokens" in df:
        ax2 = ax.twinx()
        ax2.plot(it, df["tokens"].astype(float).cumsum(), color="#54A24B", alpha=0.5, label="cum. tokens")
        ax2.set_ylabel("cumulative tokens")

    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Analyze an autoresearch run log.")
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--plateau-window", type=int, default=4)
    ap.add_argument("--out", help="path for the convergence PNG (default research/runs/<exp>.png)")
    args = ap.parse_args()

    df = load_runs(args.experiment)
    stats = summarize(df, plateau_window=args.plateau_window)

    width = max(len(k) for k in stats)
    print(f"── {stats['experiment']} " + "─" * 40)
    for k, v in stats.items():
        if isinstance(v, float):
            v = "nan" if v != v else f"{v:.4g}"  # noqa: PLR0124 (NaN check)
        print(f"  {k.ljust(width)}  {v}")

    out = args.out or os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "runs", f"{args.experiment}.png")
    )
    saved = plot(df, out)
    print(f"  {'plot'.ljust(width)}  {saved or 'skipped (matplotlib unavailable)'}")


if __name__ == "__main__":
    main()
