#!/usr/bin/env python3
"""CLI wrapper around faster-whisper. faster-whisper has no console-script
entry point of its own -- this fills that gap for this skill."""
import argparse
import sys

from faster_whisper import WhisperModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe audio/video with faster-whisper.")
    parser.add_argument("audio", help="Path to an audio or video file (any ffmpeg-readable format).")
    parser.add_argument("--model", default="large-v3", help="Model size/name (default: large-v3).")
    parser.add_argument("--device", default="cpu", help="cpu or cuda (default: cpu).")
    parser.add_argument("--compute-type", default="int8", help="int8, int8_float16, float16, float32 (default: int8; int8 is the CPU-appropriate choice).")
    parser.add_argument("--language", default=None, help="Force a language code (default: auto-detect).")
    parser.add_argument("--output", default=None, help="Write plain-text transcript here (default: stdout only).")
    args = parser.parse_args()

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    segments, info = model.transcribe(args.audio, beam_size=5, language=args.language)

    print(f"detected language: {info.language} (p={info.language_probability:.2f})", file=sys.stderr)

    lines = []
    for seg in segments:
        text = seg.text.strip()
        print(f"[{seg.start:7.2f} -> {seg.end:7.2f}] {text}")
        lines.append(text)

    if args.output:
        with open(args.output, "w") as f:
            f.write(" ".join(lines) + "\n")
        print(f"wrote transcript: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
