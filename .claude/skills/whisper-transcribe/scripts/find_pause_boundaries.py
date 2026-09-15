#!/usr/bin/env python3
"""Rank the gaps between transcript segments to find candidate chapter/track
boundaries in a single continuous recording assembled from separate pieces.

Rationale (validated on a real 7.9h course transcript): genuine track/chapter
joins show up as a handful of gaps that are BOTH large AND isolated outliers
AND suspiciously round numbers (e.g. exactly 30.00s, 31.00s), clearly
separated from a dense cluster of smaller, natural pauses (typically <15s,
from repeated-phrase drilling or ordinary speech pauses) that occur far more
often and don't share that round-number signature. This script does the
ranking; deciding which gaps are real boundaries is a judgment call --
inspect the printed context (text before/after) rather than trusting a
fixed threshold. A verified example: 5 gaps of 30-31s stood completely
isolated from ~50 other gaps of 8-24s, and each one landed exactly where
the subject matter changed.

Usage:
    python3 find_pause_boundaries.py transcript.txt [--top N] [--context K]

transcript.txt must be in the `[HH:MM:SS.mmm --> HH:MM:SS.mmm]  text` format
that transcribe.py / chunked_transcribe.py produce.
"""
import argparse
import re


def parse_hms(s):
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def fmt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--top", type=int, default=30, help="How many largest gaps to print.")
    ap.add_argument("--context", type=int, default=1, help="Segments of text to show before/after each gap.")
    args = ap.parse_args()

    segments = []
    with open(args.transcript) as f:
        for line in f:
            m = re.match(r"\[([\d:.]+) --> ([\d:.]+)\]\s*(.*)", line)
            if m:
                segments.append((parse_hms(m.group(1)), parse_hms(m.group(2)), m.group(3).strip()))

    if len(segments) < 2:
        print("Not enough segments to compute gaps.")
        return

    gaps = []
    for i in range(1, len(segments)):
        gap = segments[i][0] - segments[i - 1][1]
        gaps.append((gap, i))

    gaps.sort(key=lambda g: -g[0])
    print(f"{len(segments)} segments, {len(gaps)} gaps. Top {args.top} largest:\n")
    for gap, i in gaps[:args.top]:
        before = " / ".join(s[2][-40:] for s in segments[max(0, i - args.context):i])
        after = " / ".join(s[2][:40] for s in segments[i:i + args.context])
        print(f"gap={gap:7.2f}s  at {fmt(segments[i-1][1])} -> {fmt(segments[i][0])}  "
              f"|  ...{before}  ->  {after}...")

    print(
        "\nLook for round-number gaps (e.g. exactly N.00s) that sit apart from "
        "a dense cluster of smaller ones, and confirm with more context "
        "(re-grep the transcript around the timestamp) that the subject "
        "matter actually changes there before treating it as a real boundary."
    )


if __name__ == "__main__":
    main()
