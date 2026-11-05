"""Automated checks on a rendered video. Produces out/qa.json and frames for the agent to look at."""

from __future__ import annotations

import json
from pathlib import Path

from .ffmpeg import black_segments, contact_sheet, loudness, probe, thumbnail
from .timeline import Timeline, lint_timeline

TIKTOK_UI_BOTTOM = 0.18  # bottom ~18% of a vertical frame is covered by caption/buttons UI
TIKTOK_UI_RIGHT = 0.12


def run_qa(tl: Timeline, video: Path, project: Path, voice_duration: float | None = None) -> dict:
    info = probe(video)
    expected = tl.computed_duration()
    issues: list[str] = []
    warnings = lint_timeline(tl, voice_duration)
    w, h = tl.size
    if (info.width, info.height) != (w, h):
        warnings.append(f"rendered at {info.width}x{info.height}, timeline is {w}x{h} (preview render?)")
    if abs(info.duration - expected) > 0.25:
        issues.append(f"duration {info.duration:.2f}s != timeline {expected:.2f}s")
    loud = loudness(video)
    if loud:
        if abs(loud["integrated_lufs"] + 14) > 2:
            warnings.append(f"loudness {loud['integrated_lufs']:.1f} LUFS (target -14)")
        if loud["true_peak_db"] > -0.5:
            warnings.append(f"true peak {loud['true_peak_db']:.1f} dBTP (target <= -1)")
    else:
        issues.append("no audio stream")
    blacks = [b for b in black_segments(video) if b[1] - b[0] > 0.3]
    if blacks:
        issues.append(f"black frames at {[(round(a, 2), round(b, 2)) for a, b in blacks]}")
    if tl.format == "vertical":
        for o in tl.overlays:
            if getattr(o, "position", None) == "bottom":
                warnings.append(f"{o.type}@{o.start:.1f}s is in the bottom TikTok UI zone; use 'lower' or higher")
            y = getattr(o, "y", None)
            if y is not None and y > 1 - TIKTOK_UI_BOTTOM:
                warnings.append(f"{o.type}@{o.start:.1f}s at y={y} sits under the TikTok UI")
    qa_dir = project / "out" / "qa"
    sheet = contact_sheet(video, qa_dir / "sheet.jpg", duration=info.duration, cols=6, rows=4, width=240)
    frames = []
    for o in tl.overlays[:24]:
        t = min(o.start + min(0.5, o.duration / 2), info.duration - 0.05)
        frames.append(str(thumbnail(video, qa_dir / f"overlay_{o.type}_{t:06.2f}.jpg", t, width=360)))
    report = {
        "video": str(video),
        "duration": round(info.duration, 3),
        "expected": round(expected, 3),
        "size": [info.width, info.height],
        "loudness": loud,
        "issues": issues,
        "warnings": warnings,
        "sheet": str(sheet),
        "overlay_frames": frames,
        "ok": not issues,
    }
    (project / "out" / "qa.json").write_text(json.dumps(report, indent=2))
    return report
