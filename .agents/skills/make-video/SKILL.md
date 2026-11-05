---
name: make-video
description: End-to-end procedure to turn the user's script + footage into a finished TikTok/Shorts/YouTube video with vh. Use whenever the user asks for a video.
---

# Make a video

1. **Brief.** Get: script (or topic to write one), platform/format (`vertical` 1080x1920 for TikTok/Shorts/Reels,
   `horizontal` for YouTube), style (default `raul`), voice (TTS provider or the user's own recording), footage
   folders. Ask only for what you can't infer.
2. **Footage.** `vh stats`. If the folders aren't indexed: `vh ingest <folders> --transcribe` (see `footage-search`).
3. **Project.** `vh new projects/<slug> --style <style> --format <format> --title "<title>"`.
4. **Script.** Write `script.md`. Narration is plain lines; editing notes go in `[brackets]`, `#` headings or
   `> notes` and are not spoken. Structure for short-form: hook (≤2 s) → promise → 3-5 beats → payoff → CTA/teaser.
   About 150 words/min of Spanish narration (3 min ≈ 450 words).
5. **Voice.** `vh voiceover <p> --provider elevenlabs|openai` (needs `ELEVENLABS_API_KEY`/`OPENAI_API_KEY`;
   `espeak` is an offline placeholder only). If the user recorded their voice, copy it to `<p>/audio/` and set
   `voiceover.src` in `timeline.json`.
6. **Captions.** `vh captions <p>` → `captions.json` (word timings, script spelling) and `phrases.json`.
7. **Plan shots.** `vh segments <p>` lists phrases and the shot budget. For each beat, `vh search` for footage, open
   contact sheets, pick the best moment (`sourceIn`). Prefer clips with motion; match what the narration says.
8. **Timeline.** Write `timeline.json` (see `timeline-authoring` and `creator-styles`). Then `vh validate <p>`.
9. **Iterate fast.** `vh still <p> --at <s>` for overlays, `vh conform <p> && vh render <p> --preview` for timing.
10. **Final.** `vh build <p>` → `out/final.mp4`. Follow `video-qa` until `vh qa` is clean and the frames look right.
11. **Deliver.** Report the file path, duration, and anything you weren't sure about (clip choice, facts in
    the script). Suggest a title, caption text and 3-5 hashtags for the platform.
