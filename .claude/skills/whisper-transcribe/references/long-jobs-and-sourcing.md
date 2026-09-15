# Sourcing audio and handling long transcription jobs

Everything here was learned the hard way transcribing a real 7.9-hour audio
course and a Spotify/YouTube podcast episode in this container. It extends
the base `SKILL.md` (which covers install + model choice) to the two parts
that actually go wrong on real-world requests: getting the audio in the
first place, and not falling over partway through a long file.

## 1. Getting from "a link" to a local audio file

Try these in order. Stop at the first one that gets you a real local file —
don't guess ahead.

1. **Direct file URL** (the response's `Content-Type` is `audio/*` or
   `video/*`, or the URL ends in a media extension): `curl -fSL --retry 3
   --retry-delay 3 -C - -o file.ext "$URL"`. This is the same pattern
   `fetch-model.sh` uses for model downloads, for the same reason — plain
   `curl` with retry/resume has been reliable here where raw single-shot
   downloaders have not.
2. **YouTube** (`youtube.com`, `youtu.be`): `pip3 install -U yt-dlp`, then
   `yt-dlp -x --audio-format mp3 --audio-quality 0 -o out.%(ext)s URL`.
   **Known failure mode**: this container's outbound IP gets YouTube's
   "Sign in to confirm you're not a bot" block. Neither the default nor
   `--extractor-args "youtube:player_client=android"` got past it in
   testing. yt-dlp's own suggested fix is `--cookies-from-browser` /
   `--cookies`, which requires the user's own authenticated browser session
   — not something to obtain or fake from here. **Don't spend more than one
   retry on this**: if the plain attempt fails with a bot-check error, say
   so and ask the user to download the file themselves (their own machine
   won't have this container's IP reputation problem) and upload it
   directly. Also don't try to install a JS runtime via `curl | sh` to work
   around it — that pattern gets (correctly) blocked by this environment's
   safety classifier as arbitrary remote code execution; if you hit that
   block, stop and report it rather than finding another way to pipe a
   downloaded script into a shell.
3. **DRM-streamed platforms** (Spotify, and similar apps where the audio is
   only ever a stream, never a downloadable file): don't attempt this at
   all — there is no direct-download path, and getting the raw audio out
   requires circumventing access controls, which is a real ToS/DMCA line,
   not just a technical inconvenience. Instead:
   - Get the episode's public title via oEmbed (no auth needed):
     `https://open.spotify.com/oembed?url=<episode_url>`.
   - Search for that title — many podcasts (especially
     creator-published ones) also post the same episode on YouTube or an
     open RSS/Apple Podcasts feed. If you find a legitimate open copy, go
     to step 1 or 2 with that instead.
   - If nothing legitimate turns up, say so plainly and ask the user to
     get the file themselves (their own Spotify app, another platform,
     however) and upload it.
4. **User already has the file**: this is the easy, no-friction case (a
   direct upload) — always prefer asking for this over spending time on
   steps 1-3 if the source looks likely to be blocked (DRM, or a platform
   already known to bot-block this container).

## 2. Long files: why a single big job breaks, and what to do instead

Two independent failure modes showed up transcribing a 7.9-hour file. Both
are silent (no clear error pointing at the real cause), so if a long job
disappears or the process is gone with no output, suspect one of these
before anything else:

### 2a. The container gets reclaimed after ~45 minutes idle

A `nohup long_job.py & disown`, followed by ending the turn to wait for a
scheduled check-in, does **not** survive: after \~45 minutes with no active
tool calls, the whole container was recycled (confirmed via `uptime` showing
under 2 minutes and fresh boot messages in `dmesg`) and the orphaned process
was gone with it, despite the scratchpad's files (on a separate persistent
volume) surviving fine.

What **does** survive multi-hour idle gaps: a single Bash tool call that
runs long and gets auto-backgrounded by the harness itself (not manually
detached). One such call ran unattended for over 3 hours and completed
normally. The difference appears to be that the platform's own background-
task tracking needs the container alive to eventually deliver the
completion notification, while a bare orphaned OS process is invisible to
it and gets reclaimed with everything else.

**Practical rule**: never `nohup ... & disown` a transcription job you plan
to walk away from. Either let one real tool call run long (it will
auto-background past the ~590-600s single-call ceiling on its own — that's
fine, just wait for the completion notification), or use the resumable
per-chunk design below so that even if a gap does happen, nothing is lost
and a scheduled wake-up just picks up where it left off.

### 2b. Loading hours of audio into one `transcribe()` call can OOM

Passing an entire multi-hour file straight to
`WhisperModel.transcribe()` was killed by the kernel OOM-killer partway
through (observed: `anon-rss:13951040kB` before the cgroup limit killed it,
on a container with 15GB total RAM) — almost certainly from decoding the
whole file's audio/features into memory at once rather than streaming it.

**Fix**: split first, transcribe chunk-by-chunk. `scripts/chunked_transcribe.py`
in this skill does this — it splits the input into N-minute pieces via
`ffmpeg -f segment` (stream-copy, no re-encode, so it's fast and lossless),
transcribes one chunk at a time with the model loaded once and reused across
chunks, and checkpoints progress after every single chunk to
`resume_state.json`. 900s (15min) chunks kept each chunk's transcription
comfortably under the single-tool-call ceiling for `large-v3`/`medium` on
this box's CPU; scale down for a slower model/bigger safety margin.

```bash
python3 .claude/skills/whisper-transcribe/scripts/chunked_transcribe.py \
  path/to/long-file.mp3 --model large-v3 --language en
# Re-run the exact same command to resume after any interruption --
# it reads resume_state.json and continues from the next unprocessed chunk.
# Pass --max-chunks-this-run N to deliberately process only part of the
# file per invocation (useful when driving it across scheduled wake-ups).
```

If you do have to drive this across multiple scheduled check-ins (file is
long enough that even one auto-backgrounded call feels too big a bet), have
each wake-up read `resume_state.json`, run a bounded number of chunks via
`--max-chunks-this-run`, and reschedule the next check-in itself — but check
first whether a previous invocation is still actually running (`ps aux |
grep chunked_transcribe`) before starting a second one; two processes
writing to the same `transcript.txt`/`resume_state.json` concurrently will
corrupt both.

### 2c. Batched inference can silently drop repeated content

`faster_whisper.BatchedInferencePipeline` looked like a free speed-up (its
VAD-based chunking can approach a much smaller model's speed while keeping
the bigger model's weights), but on content with intentionally repeated or
near-identical sentences (drilling exercises, refrains), it silently
dropped whole repeated lines that the plain (non-batched) `transcribe()`
path on the same audio got right. Confirmed side-by-side on the same
15-minute range: the batched pipeline reproduced maybe half the drilled
lines. Not used in `chunked_transcribe.py` for this reason — if you're
tempted to add it back for speed, verify output against the non-batched
path on a sample of the *actual* content first, not just a generic test
clip.

## 3. Finding natural chapter/track boundaries in one continuous recording

If a long recording was originally separate tracks/files concatenated into
one (common for ripped audio courses/audiobooks), the joins often show up
as unusually long, suspiciously round-numbered, isolated pauses — distinct
from the shorter, more frequent, less regular pauses that occur naturally
throughout normal speech or repeated drilling. `scripts/find_pause_boundaries.py`
ranks a transcript's inter-segment gaps and prints surrounding text so you
can judge which ones are real:

```bash
python3 .claude/skills/whisper-transcribe/scripts/find_pause_boundaries.py transcript.txt --top 40
```

Validated example: 5 gaps of almost exactly 30-31 seconds stood completely
apart from ~50 other gaps in the 8-24s range, and every one of the 5 landed
exactly where the subject matter changed. The 8-24s gaps, despite some being
individually larger than others further down the list, were just repetition
pauses within a single ongoing topic — round numbers isolated from a
cluster are the signal, not gap size alone.

Once you have real boundary timestamps, split with stream-copy (fast,
lossless) at the midpoint of each gap:

```bash
ffmpeg -y -ss <midpoint> -to <next_midpoint> -i source.mp3 -c copy "part_N.mp3"
```

To reverse this later (e.g. re-merge pieces that got sub-split only for
delivery, see below), use the concat demuxer rather than plain `cat` —
verified to reconstitute the original almost exactly (a real test: 26ms and
260 bytes of difference over a 34-minute piece, from header overhead only,
no content lost or duplicated):

```bash
printf "file '%s'\n" part_1a.mp3 part_1b.mp3 part_1c.mp3 > filelist.txt
ffmpeg -f concat -safe 0 -i filelist.txt -c copy part_1_merged.mp3
```

## 4. Delivering the result

`SendUserFile` has a **30MB per-file cap**. A long transcript's audio parts
routinely exceed this even after chapter-splitting. Don't lower the audio
quality/bitrate to force a fit — instead sub-split the oversized piece
further, snapped to real transcript pause points (never a mid-word cut), at
roughly 25MB targets to leave headroom:

```bash
python3 - <<'EOF'
# 1. Parse transcript.txt for segment (start, end) pairs.
# 2. Compute gap midpoints as candidate cut points (same idea as
#    find_pause_boundaries.py, just every gap, not only the largest).
# 3. For a part of duration D bytes-at-current-bitrate, pick
#    n = ceil(size_MB / 25) pieces, target evenly spaced cut points,
#    and snap each one to the nearest actual gap midpoint.
EOF
```

Name the resulting pieces clearly (e.g. `02a`, `02b`, `02c` for part 2 of 3)
and tell the user explicitly which files belong together and in what order,
so they can merge them back with the concat-demuxer command above if they
want the single original file.
