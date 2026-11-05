---
name: insta360
description: Use Insta360 / 360° footage in vh — exports, reframing by yaw/pitch/fov, and choosing angles from equirectangular contact sheets.
---

# Insta360 footage

- `.insv` are raw dual-fisheye files: export them first in Insta360 Studio as either
  - **360 MP4 (equirectangular, 2:1)** → reframe in vh (flexible, any angle), or
  - **reframed flat MP4** (keyframed in Studio/app) → use like any phone clip.
  Put exports next to the originals and `vh ingest` the folder; `.lrv`/`.thm` proxies are skipped automatically.
- Equirect clips show `orientation: equirect` (`vh search --orientation equirect`). Their contact sheets show the
  whole sphere: center = forward (yaw 0), left/right edges = behind (yaw ±180), top = sky.

Reframe a shot:

```json
{"id": "s07", "source": "c_ab12...", "start": 14.2, "duration": 2.5, "sourceIn": 33,
 "reframe": {"yaw": -60, "pitch": -10, "roll": 0, "fov": 100}}
```

- `yaw`: degrees left(-)/right(+) from the camera's forward. Estimate from the contact sheet: x position
  `p` (0-1) across the frame → `yaw ≈ (p - 0.5) * 360`.
- `pitch`: up(+)/down(-). Selfie-stick shots often look best at pitch -5 to -15.
- `fov`: 80-110 natural, 120-150 "tiny planet"-ish wide.
- Check the angle cheaply: `vh conform <p>` then `vh still <p> --at <shot start + 0.5>`.
- 5.7K/8K equirect decodes slowly; conform runs once per shot and is cached.
