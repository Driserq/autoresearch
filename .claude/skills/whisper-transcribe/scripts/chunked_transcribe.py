#!/usr/bin/env python3
"""Resumable, memory-bounded transcription for long audio/video.

Why this exists (see references/long-jobs-and-sourcing.md for the full story):
- Loading hours of audio into one faster_whisper .transcribe() call OOMs on
  this container (observed: killed at ~14GB RSS transcribing a 7.9h file).
- A detached background process (nohup ... & disown) does NOT survive this
  container's ~45min-idle reclaim -- confirmed via dmesg/uptime after a
  scheduled wake-up found the process gone with no error, uptime reset to
  under 2 minutes. The platform's own native backgrounding (a Bash tool call
  that runs long and gets auto-backgrounded) DOES survive multi-hour idle
  gaps -- it must be keeping the container alive to deliver the completion
  notification. So: never nohup+disown a long transcription; let a single
  tool call run long and get auto-backgrounded, or call this script
  repeatedly (each call below the ~600s single-call ceiling) and let a
  scheduled wake-up resume it.
- faster_whisper's BatchedInferencePipeline can silently DROP entire
  repeated lines on drilling/repetitive content (confirmed: a language-course
  batch run dropped ~7 consecutive near-duplicate sentences that the
  non-batched path transcribed correctly). Not used here for that reason.

Usage:
    python3 chunked_transcribe.py INPUT_FILE [--model large-v3] [--language en]
        [--chunk-seconds 900] [--max-chunks-this-run N] [--workdir DIR]

Safe to re-invoke: reads/writes <workdir>/resume_state.json and only ever
appends to <workdir>/transcript.txt and <workdir>/transcript.srt. Splits
INPUT_FILE into <workdir>/chunks/ on first run (stream-copy, no re-encode).
Omit --max-chunks-this-run to process everything in one call (it will just
run long and get auto-backgrounded -- that's fine, see above).
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

from faster_whisper import WhisperModel


def fmt_txt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def fmt_srt(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_file")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--language", default=None, help="Force a language code; default auto-detects from the first chunk only.")
    ap.add_argument("--chunk-seconds", type=int, default=900, help="900s (15min) keeps a single chunk's transcription comfortably under the ~600s single-tool-call ceiling on this box.")
    ap.add_argument("--max-chunks-this-run", type=int, default=None, help="Process at most this many chunks then exit (for resuming across wake-ups). Default: all remaining.")
    ap.add_argument("--workdir", default=None, help="Default: '<input_file>.chunks' next to the input.")
    args = ap.parse_args()

    workdir = args.workdir or (args.input_file + ".chunks")
    chunks_dir = os.path.join(workdir, "chunks")
    state_path = os.path.join(workdir, "resume_state.json")
    txt_path = os.path.join(workdir, "transcript.txt")
    srt_path = os.path.join(workdir, "transcript.srt")
    os.makedirs(workdir, exist_ok=True)

    if not os.path.isdir(chunks_dir) or not glob.glob(os.path.join(chunks_dir, "chunk_*.mp3")):
        print(f"Splitting {args.input_file} into {args.chunk_seconds}s chunks...", file=sys.stderr)
        os.makedirs(chunks_dir, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-i", args.input_file, "-f", "segment",
             "-segment_time", str(args.chunk_seconds), "-c", "copy",
             os.path.join(chunks_dir, "chunk_%04d.mp3"), "-loglevel", "error"],
            check=True,
        )

    chunk_files = sorted(glob.glob(os.path.join(chunks_dir, "chunk_*.mp3")))
    if not chunk_files:
        print("No chunks produced -- is the input file valid audio/video?", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(state_path):
        with open(state_path) as f:
            state = json.load(f)
    else:
        state = {"done": 0, "offset": 0.0}

    n_this_run = 0
    model = None
    t_run_start = time.time()

    with open(txt_path, "a") as ftxt, open(srt_path, "a") as fsrt:
        srt_content = open(srt_path).read().strip() if os.path.exists(srt_path) else ""
        srt_idx = len(srt_content.split("\n\n")) if srt_content else 0

        while state["done"] < len(chunk_files):
            if args.max_chunks_this_run is not None and n_this_run >= args.max_chunks_this_run:
                break

            chunk_path = chunk_files[state["done"]]
            t0 = time.time()
            if model is None:
                model = WhisperModel(args.model, device="cpu", compute_type="int8")
            t_load = time.time() - t0

            duration = probe_duration(chunk_path)
            segments, info = model.transcribe(chunk_path, beam_size=5, language=args.language)

            n_segs = 0
            for seg in segments:
                n_segs += 1
                srt_idx += 1
                abs_start = seg.start + state["offset"]
                abs_end = seg.end + state["offset"]
                text = seg.text.strip()
                ftxt.write(f"[{fmt_txt(abs_start)} --> {fmt_txt(abs_end)}]  {text}\n")
                ftxt.flush()
                fsrt.write(f"{srt_idx}\n{fmt_srt(abs_start)} --> {fmt_srt(abs_end)}\n{text}\n\n")
                fsrt.flush()

            state["offset"] += duration
            state["done"] += 1
            with open(state_path, "w") as f:
                json.dump(state, f)

            n_this_run += 1
            print(f"chunk {state['done']}/{len(chunk_files)} done: {n_segs} segments, "
                  f"model_load={t_load:.1f}s chunk_time={time.time()-t0:.1f}s, "
                  f"offset now {fmt_txt(state['offset'])}", flush=True)

    if state["done"] >= len(chunk_files):
        print(f"ALL_DONE {len(chunk_files)} chunks, total audio {fmt_txt(state['offset'])} -> "
              f"{txt_path} / {srt_path}", flush=True)
    else:
        print(f"PARTIAL: {state['done']}/{len(chunk_files)} chunks done this session "
              f"({n_this_run} processed in {time.time()-t_run_start:.0f}s). "
              f"Re-run the same command to continue.", flush=True)


if __name__ == "__main__":
    main()
