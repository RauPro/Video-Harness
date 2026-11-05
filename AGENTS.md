# Video-Harness — agent guide

You are the editor. The user gives you footage (phone clips, an Insta360 disk) and a script; you deliver a finished
TikTok / Shorts / YouTube video. **You decide; `vh` executes.** Never hand-write ffmpeg pipelines or React for an
edit: everything an edit needs is expressed in `timeline.json` (schema: `schemas/timeline.schema.json`, model:
`vh/timeline.py`).

## Pipeline

```
vh ingest <folders>            # once per disk/folder; incremental, files stay where they are
vh new projects/<slug> --style raul --format vertical
  write projects/<slug>/script.md
vh voiceover projects/<slug> --provider elevenlabs   # or record your own voice and skip this
vh captions projects/<slug> [--audio my_voice.m4a]   # captions.json + phrases.json (word timings)
vh segments projects/<slug>    # phrases + shot budget for the style
vh search "..."; vh show <id>  # find shots; LOOK at the contact sheet before using a clip
  write projects/<slug>/timeline.json
vh build projects/<slug>       # validate -> conform -> render -> qa
```

Use the skills in `.agents/skills/` (also linked as `.claude/skills/`):

| Skill | When |
| --- | --- |
| `make-video` | The user asks for a video. End-to-end procedure. |
| `script-writing` | Writing or tightening `script.md`: hooks, structure, word budget, CTA, Raul's voice. |
| `footage-search` | Indexing, finding and describing clips. |
| `timeline-authoring` | Writing/editing `timeline.json`: shots, overlays, SFX, music. |
| `creator-styles` | Picking/applying a style (`raul`, `eric-struk`, `luisito`, `sam-tyler`) or adding one. |
| `video-qa` | After every render: read `out/qa.json`, look at frames, fix, re-render. |
| `insta360` | Any 360 footage (reframing, exports). |

## Rules

- Always look at contact sheets (`vh show <id>` prints the path) before choosing a clip, and at
  `out/qa/sheet.jpg` + `out/qa/overlay_*.jpg` after rendering. Fix what you see.
- Cut on phrase boundaries from `phrases.json`; respect the style's pacing (`vh segments`).
- Keep the hook (first 2 s) visual and loud: kinetic text or a price stamp + a strong shot.
- `vh validate` must be clean before `vh build`. `vh qa` must report `ok`.
- Use `vh render --preview` / `vh still --at <s>` for quick iterations; full render at the end.
- Never delete or move the user's footage. The catalog only references it.
- Captions default to Spanish (`--language es`); change per project if the script is in another language.

## Development

```
uv sync && (cd renderer && npm ci)
uv run ruff check . && uv run ruff format --check . && uv run pytest
(cd renderer && npm run typecheck)
uv run python scripts/make_demo.py /tmp/demo && uv run vh build /tmp/demo   # end-to-end check
```

After changing `vh/timeline.py`, run `uv run vh schema` and mirror the change in `renderer/src/types.ts`.
