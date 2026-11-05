# Video-Harness

AI-driven video editing harness. An agent (Claude Code or Codex) turns your raw footage (phone clips, an
Insta360 disk) and a script into a finished TikTok / Shorts / YouTube video: it searches the footage, writes the
edit as a `timeline.json`, and `vh` renders it with captions, transitions, animated overlays, SFX, music ducking
and loudness mastering.

```
footage ──vh ingest──▶ catalog (SQLite, files stay in place)
script.md ──vh voiceover──▶ voice ──vh captions──▶ word timings + phrases
agent: vh search / vh show (contact sheets) ──▶ timeline.json
vh build: validate ─▶ conform (ffmpeg: cut, crop, 360 reframe, H.264) ─▶ render (Remotion) ─▶ qa
```

Styles are modeled on the editing grammar of Eric Struk, Luisito Comunica and Sam Tyler (pacing measured from
their videos), plus a `raul` house style that mixes them. See `.agents/skills/creator-styles/SKILL.md`.

## Install

Requirements: Python 3.11+ with [uv](https://docs.astral.sh/uv/), Node.js 20+ (22 recommended), ffmpeg.
Optional: `espeak-ng` (offline placeholder voice), `ELEVENLABS_API_KEY` / `OPENAI_API_KEY` for real TTS.

```
git clone https://github.com/RauPro/Video-Harness && cd Video-Harness
uv sync
uv run vh setup     # renderer npm deps + built-in SFX
uv run vh doctor
```

Run it on the computer the footage disk is plugged into. The catalog lives in `~/.vh/` (override with
`VH_DATA`, `VH_CATALOG`, `VH_CACHE`).

`vh init` creates your workspace (`~/VideoHarness`, or `VH_WORKSPACE`, e.g. on the external disk):

```
footage/phone, footage/insta360   raw footage (optional: vh ingest indexes any folder in place, nothing is copied)
assets/music|sfx|images|brand     reusable assets; vh assets tag <file> --mood chill --license "..."
projects/<date>-<slug>/           one folder per video (vh new <slug>), with out/final.mp4
published/<date>-<slug>/          what you posted: final.mp4 + meta.json with url and views (vh publish / vh published)
ideas/<slug>.md                   video ideas proposed from your footage (vh ideas)
```

The catalog also records which clips each video used, so `vh search --unused` and `vh ideas` show fresh footage.

## Use with an agent

Open the repo in Claude Code or Codex and ask, for example:

> Make a 60 s vertical video in my style from projects/bangkok/script.md using my footage in
> /Volumes/Insta360/2026-thailand and ~/Phone/DCIM.

> What videos can I make from my Thailand footage that I haven't used yet?

The agent follows `AGENTS.md` (Claude Code reads it via `CLAUDE.md`) and the skills in `.agents/skills/`
(symlinked to `.claude/skills/`): `make-video`, `video-ideas`, `script-writing`, `footage-search`, `timeline-authoring`,
`creator-styles`, `video-qa`, `insta360`.

## Use by hand

```
uv run vh ingest /Volumes/Insta360 ~/Phone/DCIM --transcribe
uv run vh ideas --unused                     # what can I make from footage I haven't used?
uv run vh new projects/bangkok --style raul --format vertical
$EDITOR projects/bangkok/script.md
uv run vh voiceover projects/bangkok --provider elevenlabs
uv run vh captions projects/bangkok
uv run vh segments projects/bangkok
uv run vh search "street food night" --orientation vertical
$EDITOR projects/bangkok/timeline.json
uv run vh build projects/bangkok          # -> projects/bangkok/out/final.mp4
```

`uv run vh --help` lists all commands. `cd renderer && npx remotion studio` opens a live preview (with
`--props <project>/out/props.json` after a render, or a built-in demo of every overlay).

## Demo

```
uv run python scripts/make_demo.py /tmp/demo   # synthetic footage + offline voice + auto timeline
uv run vh build /tmp/demo
```

## Development

```
uv run ruff check . && uv run ruff format --check . && uv run pytest
cd renderer && npm run typecheck
```

`vh/timeline.py` is the source of truth for the timeline format; after changing it run `uv run vh schema` and
update `renderer/src/types.ts`.

## Notes

- Use music and footage you have rights to. Platform library sounds (TikTok/YouTube) can't be embedded; add
  them in the app after upload if needed.
- Remotion is free for individuals and small teams; larger companies need a
  [company license](https://www.remotion.dev/license).
