---
name: creator-styles
description: The editing styles available in vh (raul, eric-struk, luisito, sam-tyler), what each looks like, and how to add or tune a style from a reference video.
---

# Creator styles

Styles live in `styles/<name>/theme.json` (fonts, colors, caption preset, pacing, default SFX, music levels) and
can `extends` another style. Set `"style"` in `timeline.json`. `vh styles` lists them.

Pacing below was measured from reference videos with `vh analyze-ref` (average shot length).

## raul (default)
Spanish travel/Thailand. Eric's caption punch + Luisito's lower-thirds and reveals + Sam's list headers.
3-word bold-pop captions, center. ~2.4 s shots. Hook: `kineticText` xl + strongest shot. Beats: `listHeader`.
Prices: `priceStamp` badge, `cash` SFX. End: `comingUp` or follow CTA.

## eric-struk
Fast travel-hack/review shorts (~2.2 s shots on Shorts, ~2.35 s long-form). 1-2 word ALL-CAPS captions with
yellow keyword. Signature moves: `priceStamp` badge with green `BOOKED` pill, `comingUp` teaser top-left in the
first 3 s, white `questionCard` beats, `arrowCallout` to numbers, `flash` + `cash` on reveals, `whip` every
3-4 cuts, punch-in every ~3 shots.

## luisito
Vlog energy (~2.5-2.7 s shots). Small lower captions. Signature: yellow stacked `lowerThird` (kicker/title/
subtitle) for every new place, `imageInsert` cutouts on `paper-red` background, phone-screen inserts
(`frame: phone`), `priceStamp` slime variant with green flash, comedic `scratch`/`boom` SFX, `flash` transitions.

## sam-tyler
Bangkok expat tours/lists. Shorts ~2.2 s, long-form calm (~7.5 s shots, use 4-8 s). Sentence-case captions,
lower. Signature: blue `lowerThird` `variant: tag` name tags, numbered `listHeader` ("1. TDAC"), `infoCard`
price tables, `slide` transitions, minimal SFX.

## Add or tune a style

```
vh analyze-ref "https://www.youtube.com/watch?v=..." --name eric-short --section 0-180
```

This downloads (yt-dlp) or reads a local file and writes `references/<name>/`: cuts/min, shot length stats,
loudness and contact sheets. Look at the sheets for colors/fonts/overlay patterns, then create
`styles/<new>/theme.json` with `"extends": "<closest style>"` and override only what differs. Don't copy
creators' logos, music or footage; take the grammar (pacing, typography, overlay types), not the assets.
