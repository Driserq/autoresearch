---
name: whisper-transcribe
description: "Install and run Whisper speech-to-text in this sandbox container, and transcribe audio/video files with it. Recommends faster-whisper (verified equal quality, ~2x faster, ~4x less disk, no download bug); documents openai-whisper as a fallback. Use when asked to install Whisper, set up speech-to-text here, or transcribe an audio/video file in this environment."
---

# Whisper transcription in this container

Setup and usage validated directly in this project's sandbox container (root,
Debian/Ubuntu-based, Python 3.11, apt + pip available, outbound HTTPS via a
pre-configured proxy). Re-run the setup steps in any fresh container — nothing
here persists across sessions; the container is ephemeral and none of this is
part of the `autoresearch` product itself (don't add it to `claude-plugin/`,
`.opencode/`, or `.agents/` — those are the distributed plugin, synced only by
`scripts/transform.sh` for the `autoresearch` skill).

## This container's constraints

- **No GPU.** `torch.cuda.is_available()` is `False`. Everything runs on CPU
  (4 vCPUs, 15GB RAM observed). Budget accordingly — see timings below.
- **Disk is a fixed, limited allowance** (~30GB free observed at session
  start).
- **root** is available, so `apt-get install` works directly.

## Recommendation: use faster-whisper, not openai-whisper

Both were installed and benchmarked here on the exact same model
(`large-v3`) and the exact same 59-second test video. Verdict: **faster-whisper**.

| | faster-whisper (int8) | openai-whisper |
|---|---|---|
| Transcript output | Identical text and segment timings | (baseline) |
| Total wall time, warm cache | 139s | 279s (~2x slower) |
| Model download | Succeeded first try, both times (huggingface_hub) | **Failed its SHA256 checksum twice in a row** (see below) |
| Disk footprint (deps + large-v3 weights) | ~2.9GB cache, no CUDA libs pulled in | ~13GB (pulls full CUDA runtime even with no GPU to use it) |
| System deps | none required beyond the pip package | needs `ffmpeg` installed via apt |
| CLI | none shipped — use `scripts/transcribe.py` in this skill | `whisper` console script |

The quality claim is not an estimate: `model.transcribe()` on `large-v3`
produced text and per-segment start/end timestamps that matched
openai-whisper's `large-v3` output exactly, word for word, timestamp for
timestamp, on real speech audio (not just a synthetic test). int8
quantization cost nothing measurable here.

### Setup (verified working)

```bash
pip3 install -U faster-whisper
```

That's it — no system `ffmpeg` install needed (it decodes via the bundled
PyAV/`av` package), no CUDA libraries pulled in, no separate model-fetch step.

### Transcribing

```bash
python3 .claude/skills/whisper-transcribe/scripts/transcribe.py path/to/file.mp4
# --model tiny|base|small|medium|large-v3|... (default: large-v3)
# --compute-type int8|int8_float16|float16|float32 (default: int8 — right choice for CPU)
# --language en (default: auto-detect)
# --output transcript.txt (optional; segments always print to stdout)
```

It prints `[start -> end] text` per segment to stdout (detected language goes
to stderr), same shape as the openai-whisper CLI's console output.

## Fallback: openai-whisper

Documented in case something specifically needs the reference CLI/implementation.
Slower, heavier, and its own model downloader is unreliable here — use this
only if faster-whisper doesn't work for your use case.

### Setup

```bash
apt-get update -qq && apt-get install -y ffmpeg
pip3 install -U openai-whisper
```

### Known issue: openai-whisper's own model downloader corrupts large checkpoints here

`whisper`'s built-in downloader (`whisper.load_model`, and the `whisper` CLI)
fetches checkpoints with raw `urllib.request`, reading 8KB at a time over one
very long-lived HTTPS connection, then checks the SHA256 only after the whole
file is written. In this environment, downloading `large-v3.pt` (2.9GB) this
way **failed its checksum twice in a row**, with a different wrong hash and a
slightly different file size each time — i.e. non-deterministic silent
corruption during the transfer, not a one-off blip. The proxy's own status
endpoint (`curl -sS http://127.0.0.1:41637/__agentproxy/status`) showed zero
recorded relay failures for either attempt, so the proxy doesn't consider
this an error. (This is presumably why faster-whisper's huggingface_hub-based
downloader — a proper chunked, resumable client — had no trouble with the
same size of download, twice.)

`curl` (with `--retry`/`-C -` resume) fetching the exact same URL through the
same proxy succeeded with a correct checksum on the first try. So: **don't
let the `whisper` CLI download models on its own** — pre-fetch and verify
with curl, into whisper's own cache dir, and it'll find the file already
there and skip its downloader entirely.

`scripts/fetch-model.sh` in this skill does exactly that for any model size:

```bash
.claude/skills/whisper-transcribe/scripts/fetch-model.sh large-v3
# tiny | tiny.en | base | base.en | small | small.en | medium | medium.en
# | large-v1 | large-v2 | large-v3 | large-v3-turbo (also: large, turbo)
```

It's idempotent — safe to re-run; it checks the existing file's hash before
re-downloading anything.

### Transcribing

```bash
whisper path/to/file.mp4 --model large-v3 --fp16 False --output_dir ./out
```

`--fp16 False` is required on CPU (there's no GPU to run fp16 on; omitting it
just prints a warning and falls back automatically, but pass it explicitly).
Output formats default to txt + vtt + srt + tsv + json in `--output_dir`.

## Measured performance (this container, 4 vCPUs, no GPU)

Timed against the same real 59-second video (English speech):

| Model | Implementation | Wall time | Relative speed |
|---|---|---|---|
| `tiny` | openai-whisper | 8.1s | ~7.3x faster than realtime |
| `tiny` | faster-whisper | ~5s | faster than openai-whisper `tiny`, similar accuracy |
| `large-v3` | faster-whisper (int8) | 139s (warm cache) | ~2.4x slower than realtime |
| `large-v3` | openai-whisper | 279s (warm cache) | ~4.7x slower than realtime |

For anything longer than a short clip, `tiny` or `base` are still the right
choice when turnaround time matters more than maximum accuracy. Reach for
`large-v3` (via faster-whisper) when accuracy matters most — it's still not
fast on this CPU-only box, but it's the best quality/speed tradeoff available
here for that model size.

## Quick end-to-end smoke test

```bash
pip3 install -U faster-whisper
ffmpeg -y -f lavfi -i "anullsrc=r=16000:cl=mono" -t 3 /tmp/smoke.wav 2>/dev/null || \
  python3 -c "import wave,struct; w=wave.open('/tmp/smoke.wav','w'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(b'\x00\x00'*16000*3); w.close()"
python3 .claude/skills/whisper-transcribe/scripts/transcribe.py /tmp/smoke.wav --model tiny
```

(The `python3 -c` fallback avoids a hard dependency on system `ffmpeg` being
installed, since faster-whisper doesn't otherwise need it.)
