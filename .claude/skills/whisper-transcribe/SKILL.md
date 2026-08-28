---
name: whisper-transcribe
description: "Install and run OpenAI's openai-whisper speech-to-text in this sandbox container, and transcribe audio/video files with it. Use when asked to install Whisper, set up speech-to-text here, or transcribe an audio/video file in this environment."
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
- **ffmpeg is not preinstalled.** `openai-whisper` needs it to decode audio.
- **Disk is a fixed, limited allowance** (~30GB free observed at session
  start). `pip install openai-whisper` pulls full CUDA runtime libraries by
  default even though there's no GPU to use them — it cost ~13GB combined
  with the large-v3 weights in testing. If disk is tight, install the
  CPU-only torch wheel first: `pip3 install torch --index-url
  https://download.pytorch.org/whl/cpu`, then `pip3 install openai-whisper`
  (not re-verified this session, but a standard, well-documented PyTorch
  pattern).
- **root** is available, so `apt-get install` works directly.

## One-time setup (verified working)

```bash
apt-get update -qq && apt-get install -y ffmpeg
pip3 install -U openai-whisper
```

## Known issue: openai-whisper's own model downloader corrupts large checkpoints here

`whisper`'s built-in downloader (`whisper.load_model`, and the `whisper` CLI)
fetches checkpoints with raw `urllib.request`, reading 8KB at a time over one
very long-lived HTTPS connection, then checks the SHA256 only after the whole
file is written. In this environment, downloading `large-v3.pt` (2.9GB) this
way **failed its checksum twice in a row**, with a different wrong hash and a
slightly different file size each time — i.e. non-deterministic silent
corruption during the transfer, not a one-off blip. The proxy's own status
endpoint (`curl -sS http://127.0.0.1:41637/__agentproxy/status`) showed zero
recorded relay failures for either attempt, so the proxy doesn't consider
this an error.

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

## Transcribing

`whisper` accepts audio or video directly (it shells out to ffmpeg to decode
whatever container/codec you give it):

```bash
whisper path/to/file.mp4 --model large-v3 --fp16 False --output_dir ./out
```

`--fp16 False` is required on CPU (there's no GPU to run fp16 on; omitting it
just prints a warning and falls back automatically, but pass it explicitly).
Output formats default to txt + vtt + srt + tsv + json in `--output_dir`.

## Measured performance (this container, 4 vCPUs, no GPU)

Timed against a real 59-second video (English speech) and a synthetic
silence clip:

| Model | Wall time for 59s audio | Relative speed | Cold-load overhead |
|---|---|---|---|
| `tiny` | 8.1s | ~7.3x faster than realtime | small, folded into the 8.1s |
| `large-v3` | 4m39s (279s) | ~4.7x slower than realtime | ~48s just to load the model, before any audio is processed |

`tiny`'s transcript on the test video was substantively accurate (same
content, minor wording/punctuation differences from `large-v3`). For
anything longer than a short clip on this CPU-only box, `tiny` or `base` are
usually the right default — reach for `large-v3` only when accuracy matters
more than turnaround time, and expect multi-minute waits per minute of audio.

## Quick end-to-end smoke test

```bash
apt-get install -y ffmpeg && pip3 install -U openai-whisper
.claude/skills/whisper-transcribe/scripts/fetch-model.sh tiny
ffmpeg -y -f lavfi -i "anullsrc=r=16000:cl=mono" -t 3 /tmp/smoke.wav
whisper /tmp/smoke.wav --model tiny --fp16 False --output_dir /tmp/whisper-smoke
```
