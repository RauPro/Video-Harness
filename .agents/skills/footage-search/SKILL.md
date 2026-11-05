---
name: footage-search
description: Index the user's phone/Insta360 footage into the vh catalog, find clips by content, and annotate them. Use before choosing shots.
---

# Footage search

The catalog (`~/.vh/catalog.db`, override with `VH_CATALOG`) references files in place; nothing is copied.

## Index

```
vh ingest "/Volumes/Insta360" "~/Pictures/Phone" --workers 4      # incremental; re-run any time
vh ingest <folder> --transcribe                                    # also Whisper-transcribe clips with speech
vh stats
```

Per clip it stores: duration, size, fps, codec, orientation (`vertical|horizontal|square|equirect`), audio,
creation date, GPS location, device, scene-change times, a thumbnail and a contact sheet. Insta360 `.lrv`/`.thm`
proxies are skipped. Raw `.insv` files are indexed but must be exported from Insta360 Studio before use
(see `insta360`).

## Find

```
vh search "pad thai mercado"                     # transcript / description / tags / path / location
vh search --orientation vertical --min-duration 3 --after 2025-01-01
vh search --undescribed --limit 50               # clips nobody has looked at yet
vh search --unused --path 2026-thailand          # not used in any built video yet
vh search --json "playa"                         # machine-readable
vh show <id>                                     # all metadata + contact sheet path
```

## Describe (makes footage searchable by what's in it)

Open the contact sheet image from `vh show`, then:

```
vh describe <id> --text "Street food stall at night, vendor flipping pad thai, neon signs" \
  --tags "bangkok,street-food,night,vendor" --rating 4
```

Describe clips as you look at them, even ones you don't use; it pays off across videos. For big disks, describe
in batches (`--undescribed --limit 50`), prioritizing recent folders or the trip the video is about.

Use the clip id (`c_...`) as `source` in the timeline; `vh conform` resolves it to the file.
