"""Measure the editing rhythm of a reference video (yours or a creator you like)."""

from __future__ import annotations

import json
import re
import shutil
import statistics
import subprocess
from pathlib import Path

from .ffmpeg import contact_sheet, detect_scenes, loudness, probe


def fetch(url: str, dest_dir: Path, section: str | None = None) -> Path:
    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        raise RuntimeError("yt-dlp not installed (uv sync --extra download, or brew install yt-dlp)")
    dest_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        ytdlp,
        "-f",
        "bv*[height<=720]+ba/b[height<=720]/b",
        "--merge-output-format",
        "mp4",
        "-o",
        str(dest_dir / "video.%(ext)s"),
        "--no-playlist",
        "-q",
        url,
    ]
    if section:
        cmd += ["--download-sections", f"*{section}"]
    subprocess.run(cmd, check=True)
    return dest_dir / "video.mp4"


def analyze(video: Path, out_dir: Path, *, transcribe: bool = False, model: str = "small") -> dict:
    info = probe(video)
    cuts = detect_scenes(video, threshold=0.3, analysis_fps=10)
    bounds = [0.0, *cuts, info.duration]
    shots = [b - a for a, b in zip(bounds, bounds[1:], strict=False) if b - a > 0.05]
    q = statistics.quantiles(shots, n=10) if len(shots) >= 10 else [min(shots), max(shots)]
    out_dir.mkdir(parents=True, exist_ok=True)
    sheets = []
    chunk = 60.0
    for i in range(max(1, int(info.duration // chunk) + (info.duration % chunk > 5))):
        if i >= 5:
            break
        seg = out_dir / f"sheet_{i:02d}.jpg"
        tmp = out_dir / f".seg_{i}.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(i * chunk),
                "-t",
                str(chunk),
                "-i",
                str(video),
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-vf",
                "scale=480:-2",
                str(tmp),
            ],
            check=True,
        )
        sheets.append(str(contact_sheet(tmp, seg, duration=min(chunk, info.duration - i * chunk), cols=5, rows=4)))
        tmp.unlink(missing_ok=True)
    result = {
        "source": str(video),
        "duration": round(info.duration, 2),
        "orientation": info.orientation,
        "cuts": len(cuts),
        "cuts_per_minute": round(len(cuts) / (info.duration / 60), 1) if info.duration else 0,
        "shot_seconds": {
            "mean": round(statistics.mean(shots), 2),
            "median": round(statistics.median(shots), 2),
            "p10": round(q[0], 2),
            "p90": round(q[-1], 2),
        },
        "first_cut_at": round(cuts[0], 2) if cuts else None,
        "loudness": loudness(video),
        "sheets": sheets,
    }
    if transcribe:
        from .transcribe import plain_text
        from .transcribe import transcribe as stt

        words, lang = stt(video, model=model)
        text = plain_text(words)
        result["language"] = lang
        result["words_per_minute"] = round(len(re.findall(r"\w+", text)) / (info.duration / 60), 1)
        result["hook_text"] = " ".join(text.split()[:40])
    (out_dir / "analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result
