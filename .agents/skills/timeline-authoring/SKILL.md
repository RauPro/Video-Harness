---
name: timeline-authoring
description: How to write timeline.json for vh — shots, fits, punch-ins, transitions, overlays (kinetic text, price stamps, lower-thirds, list headers, question cards, arrows, inserts), SFX and music.
---

# Timeline authoring

`timeline.json` is the whole edit. Times are in seconds on the output timeline. Schema:
`schemas/timeline.schema.json`. Validate with `vh validate <project>`.

```json
{
  "version": 1, "title": "Bangkok con $500", "format": "vertical", "fps": 30, "style": "raul",
  "voiceover": {"src": "audio/voice.mp3"},
  "music": {"src": "music/track.mp3", "volume": 0.18, "duckTo": 0.06},
  "captions": {"highlight": ["bangkok", "$500"]},
  "video": [
    {"id": "s01", "source": "c_1a2b3c4d5e", "start": 0, "duration": 2.1, "sourceIn": 12.4,
     "punchIns": [1.2], "grade": "vivid"},
    {"id": "s02", "source": "c_9f8e7d6c5b", "start": 2.1, "duration": 2.6, "fit": "blur",
     "transitionIn": {"type": "whip"}}
  ],
  "overlays": [
    {"type": "kineticText", "start": 0, "duration": 1.8, "text": "Bangkok con $500", "highlight": ["$500"], "sfx": "pop"}
  ],
  "sfx": [{"src": "whoosh", "start": 2.1}]
}
```

## Shots (`video[]`)

- Shots must tile the timeline: no gaps, no overlaps (`vh validate` warns). Last shot ends at voice end + ~0.3 s.
- `source`: catalog id `c_...` or a path (relative to the project or absolute). `sourceIn`: where in the source.
- `fit`: `cover` (crop to fill; default), `blur` (horizontal clip in vertical video: sharp center over blurred
  fill), `contain` (letterbox).
- `zoom: {start, end, focusX, focusY}`: slow Ken Burns (1.0→1.08 is subtle). `punchIns: [t]`: instant 1.15x
  punch at t seconds into the shot (`punchScale`), use on emphasized words.
- `transitionIn.type`: `cut` (default) | `whip` | `slide` | `zoom` | `flash` | `fade` | `glitch`. Use sparingly
  (every 3-5 cuts, at beat changes) and pair with an SFX (`whoosh` for whip/slide, `glitch` for glitch).
- `speed`: 0.25-4. `volume`: natural sound level (0 mutes; keep 0.2-0.5 under voice for ambience).
- `grade`: `none|warm|cool|vivid|bw|film`. `reframe`: 360 footage only (see `insta360`).

## Overlays (`overlays[]`), all with `start`, `duration`, optional `sfx`

| type | use | key fields |
| --- | --- | --- |
| `kineticText` | hook titles, punchlines | `text`, `highlight[]`, `position`, `size` m/l/xl, `animation` pop/slide/typewriter/stack |
| `priceStamp` | prices, totals, numbers | `amount`, `label`, `sublabel`, `variant` badge/bubble/slime |
| `lowerThird` | places, people | `title`, `kicker`, `subtitle`, `variant` stack (Luisito yellow) / tag (blue name tag) |
| `listHeader` | numbered beats | `number`, `title`, `subtitle` |
| `comingUp` | teaser top-left | `text` |
| `questionCard` | full-screen question beat | `kicker`, `text`, `highlight[]` (captions hide under it) |
| `flash` | white/green flash on a reveal | `color`, `opacity` |
| `arrowCallout` | point at something | `x`, `y` (0-1 tip), `angle`, `text`, `color` |
| `infoCard` | small table of facts/prices | `title`, `rows[{left,right}]` |
| `imageInsert` | screenshot/photo/phone screen | `src`, `frame` none/phone/polaroid, `background` none/paper-red/paper-blue/blur, `x`,`y`,`scale`,`rotate` |
| `emoji` | reaction | `emoji`, `x`, `y`, `size` |
| `progressBar` | retention bar | `color` |

`position`: `top|upper|center|lower|bottom`. Keep text out of the bottom 18% and right 12% on vertical
(TikTok UI); `vh qa` checks it. Captions step aside automatically under centered `priceStamp`/`kineticText`/
`infoCard` and under `questionCard`; use `captions.hideDuring: [[a,b]]` for other cases.

## Audio

- SFX `src`: built-in (`vh sfx`: whoosh, swish, pop, click, ding, cash, riser, boom, glitch, typing, shutter,
  scratch) or a file in the project. Every overlay entrance and accent transition should have one; keep volume
  0.4-0.7.
- Music: `src`, `volume`, `duckTo` (level under speech), `fadeIn`, `fadeOut`, `sourceIn`. Ducking follows the
  caption word timings. Use music the user owns or royalty-free; TikTok/YouTube library audio can't be embedded.
- Final mix is normalized to -14 LUFS / -1 dBTP.

## Timing recipe

Take `phrases.json`. One shot per phrase, split long phrases to meet the style's `avgShotSeconds`. Put overlays on
the phrase that names them (price stamp starts on the number word: find it in `captions.json`). Punch-in on the
stressed word. Start the next shot ~0-2 frames before the phrase so the cut lands with the word.
