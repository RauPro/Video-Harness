---
name: video-ideas
description: Propose video ideas from the user's indexed footage (vh ideas), grounded in what was actually filmed and in what performed best. Use when the user asks "what can I make", "give me ideas", or has footage but no script.
---

# Video ideas from footage

## 1. See what's there

```
vh stats                                  # is the footage indexed? if not: vh ingest <folders> (footage-search)
vh ideas                                  # shoots = clips grouped by date + place, unused footage first
vh ideas --unused --json                  # what hasn't been used in a built video yet (machine-readable)
vh ideas --path 2026-thailand --gap-days 1
vh published --refresh --json             # what was already posted and how many views it got
```

Each shoot has dates, a GPS centroid, clip count/minutes, `unused`, `described`, orientation mix, top tags,
`highlights` (best-rated/longest clips with contact sheets) and `speech` (what was said on camera).

## 2. Look before proposing

For the 3-5 shoots with the most unused footage, open the `highlights[].sheet` images. If a shoot has few
`described` clips, describe its best ones first (`vh describe <id> --text ... --tags ... --rating ...`), then
`vh search --path <folder> --unused` for more. Speech clips are gold: a reaction or a price said on camera can be
the hook.

## 3. Propose

Each idea must be filmable from clips that exist. Use the hook formulas and structures in `script-writing`, and
favor what performed: check `vh published --json` (views per topic) and `script-writing/analysis.md`. Raul's best
videos combine a concrete loss or contradiction, prices, and a series.

For each idea write `<workspace>/ideas/<slug>.md`:

```markdown
# <working title>
- format: vertical 60-90 s | horizontal 3-8 min      style: raul
- shoot: shoot-2026-04-10 (Bangkok)   footage: 14 clips, 9 unused
- hook (formula 2, myth question): "¿Bangkok es realmente tan barato como dicen?"
- why: prices on camera in c_1a2b, c_3c4d; budget format = Raul's #2 (225K)

## Beats
1. Hook: c_1a2b @12.0 (vendor says "50 baht") + priceStamp
2. ...
5. CTA: "¿Qué ciudad sigue? Te leo."

## Missing
- No shot of the hotel lobby. Film it or use an image insert.
```

Give the user 3-5 ideas in chat: title, hook line, length, and how much footage backs it. Mark the strongest
one. Don't write the full script until they pick.

## 4. When the user picks one

```
vh new <slug> --style raul --format vertical      # → <workspace>/projects/<date>-<slug>
```

Copy the idea's beats into `script.md` as `[editing notes]`, write the narration (`script-writing`), then
continue with `make-video`. After it ships: `vh publish <project> --platform tiktok --url <post url>` so the
clips count as used and the views feed the next round of ideas.
