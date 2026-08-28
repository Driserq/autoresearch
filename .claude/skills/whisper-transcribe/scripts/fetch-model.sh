#!/usr/bin/env bash
# Fetch an openai-whisper checkpoint via curl and verify its SHA256 before
# use. openai-whisper's own downloader (urllib.request, 8KB reads over a
# single long-lived connection) reliably corrupts large checkpoints in this
# environment's proxy setup -- two independent large-v3 downloads through it
# produced different wrong hashes. curl with retry/resume does not have this
# problem. Pre-fetching here lets `whisper` find an already-verified file in
# its cache and skip its own downloader entirely.
set -euo pipefail

MODEL="${1:-}"
CACHE_DIR="${WHISPER_CACHE_DIR:-$HOME/.cache/whisper}"

declare -A URLS=(
  [tiny.en]="https://openaipublic.azureedge.net/main/whisper/models/d3dd57d32accea0b295c96e26691aa14d8822fac7d9d27d5dc00b4ca2826dd03/tiny.en.pt"
  [tiny]="https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt"
  [base.en]="https://openaipublic.azureedge.net/main/whisper/models/25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead/base.en.pt"
  [base]="https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt"
  [small.en]="https://openaipublic.azureedge.net/main/whisper/models/f953ad0fd29cacd07d5a9eda5624af0f6bcf2258be67c92b79389873d91e0872/small.en.pt"
  [small]="https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt"
  [medium.en]="https://openaipublic.azureedge.net/main/whisper/models/d7440d1dc186f76616474e0ff0b3b6b879abc9d1a4926b7adfa41db2d497ab4f/medium.en.pt"
  [medium]="https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt"
  [large-v1]="https://openaipublic.azureedge.net/main/whisper/models/e4b87e7e0bf463eb8e6956e646f1e277e901512310def2c24bf0e11bd3c28e9a/large-v1.pt"
  [large-v2]="https://openaipublic.azureedge.net/main/whisper/models/81f7c96c852ee8fc832187b0132e569d6c3065a3252ed18e56effd0b6a73e524/large-v2.pt"
  [large-v3]="https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt"
  [large]="https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt"
  [large-v3-turbo]="https://openaipublic.azureedge.net/main/whisper/models/aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a/large-v3-turbo.pt"
  [turbo]="https://openaipublic.azureedge.net/main/whisper/models/aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a/large-v3-turbo.pt"
)

if [[ -z "$MODEL" || -z "${URLS[$MODEL]:-}" ]]; then
  echo "usage: fetch-model.sh <model-name>" >&2
  echo "known models: ${!URLS[*]}" >&2
  exit 1
fi

URL="${URLS[$MODEL]}"
EXPECTED_SHA256="$(basename "$(dirname "$URL")")"
mkdir -p "$CACHE_DIR"
TARGET="$CACHE_DIR/$(basename "$URL")"

if [[ -f "$TARGET" ]] && [[ "$(sha256sum "$TARGET" | cut -d' ' -f1)" == "$EXPECTED_SHA256" ]]; then
  echo "already present and verified: $TARGET"
  exit 0
fi

echo "fetching $MODEL -> $TARGET"
curl -fSL --retry 3 --retry-delay 3 -C - -o "$TARGET" "$URL"

ACTUAL_SHA256="$(sha256sum "$TARGET" | cut -d' ' -f1)"
if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
  echo "checksum mismatch for $MODEL: expected $EXPECTED_SHA256, got $ACTUAL_SHA256" >&2
  rm -f "$TARGET"
  exit 1
fi

echo "verified OK: $TARGET"
