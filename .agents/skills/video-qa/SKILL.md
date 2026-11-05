---
name: video-qa
description: Verify a vh render (out/qa.json, contact sheet, overlay frames) and fix issues before delivering a video.
---

# Video QA

`vh build` ends with `vh qa`; run `vh qa <project>` again after any re-render. It writes `out/qa.json`,
`out/qa/sheet.jpg` (frames across the video) and `out/qa/overlay_<type>_<t>.jpg` (one frame per overlay).

Checks: resolution, duration vs timeline/voice, integrated loudness (-14 LUFS ±1) and true peak (≤ -1 dBTP),
missing audio, black segments, text in the vertical-video UI zones (bottom 18%, right 12%).

Then **look** at the images. Checklist:

- Hook frame (t≈0.5 s) is readable without sound and visually strong.
- No caption collides with an overlay or a face; nothing cut off at edges.
- Shot content matches what the narration says at that moment.
- No near-duplicate consecutive shots; no static shot longer than the style's `maxShotSeconds`.
- Highlights/prices are on the right words; numbers in overlays match the script.
- Horizontal sources in vertical use `fit: blur` or a deliberate crop (`zoom.focusX`) that keeps the subject.

Fix in `timeline.json`, then `vh conform` (only changed shots are redone) and `vh render`. For a single
overlay, `vh still <p> --at <s>` is enough. Report anything you couldn't verify (e.g. facts in the script).
