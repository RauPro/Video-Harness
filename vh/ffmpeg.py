"""Thin wrappers around ffmpeg/ffprobe."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise FFmpegError(f"`{binary}` not found on PATH; install ffmpeg (brew install ffmpeg)")
    return path


def run(args: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, capture_output=capture, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or "")[-2000:]
        raise FFmpegError(f"command failed ({proc.returncode}): {' '.join(args[:6])} ...\n{tail}")
    return proc


def ffmpeg(*args: str) -> subprocess.CompletedProcess[str]:
    return run([require("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", *args])


@dataclass
class ProbeInfo:
    duration: float
    width: int = 0
    height: int = 0
    fps: float = 0.0
    vcodec: str | None = None
    pix_fmt: str | None = None
    rotation: int = 0
    has_video: bool = False
    has_audio: bool = False
    created_at: str | None = None
    location: str | None = None
    device: str | None = None
    raw_tags: dict[str, str] = field(default_factory=dict)

    @property
    def display_size(self) -> tuple[int, int]:
        if self.rotation % 180:
            return self.height, self.width
        return self.width, self.height

    @property
    def orientation(self) -> str:
        w, h = self.display_size
        if not w or not h:
            return "unknown"
        if abs(w / h - 2.0) < 0.02:
            return "equirect"
        if w > h * 1.05:
            return "horizontal"
        if h > w * 1.05:
            return "vertical"
        return "square"


def _fps(rate: str | None) -> float:
    if not rate or rate == "0/0":
        return 0.0
    if "/" in rate:
        n, d = rate.split("/")
        return float(n) / float(d) if float(d) else 0.0
    return float(rate)


def probe(path: Path) -> ProbeInfo:
    out = run(
        [require("ffprobe"), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    ).stdout
    data = json.loads(out)
    fmt = data.get("format", {})
    tags = {k.lower(): str(v) for k, v in (fmt.get("tags") or {}).items()}
    info = ProbeInfo(duration=float(fmt.get("duration") or 0.0), raw_tags=tags)
    for s in data.get("streams", []):
        stype = s.get("codec_type")
        if stype == "video" and not info.has_video and s.get("disposition", {}).get("attached_pic") != 1:
            info.has_video = True
            info.width = int(s.get("width") or 0)
            info.height = int(s.get("height") or 0)
            info.fps = _fps(s.get("avg_frame_rate")) or _fps(s.get("r_frame_rate"))
            info.vcodec = s.get("codec_name")
            info.pix_fmt = s.get("pix_fmt")
            rot = (s.get("tags") or {}).get("rotate")
            for sd in s.get("side_data_list") or []:
                if "rotation" in sd:
                    rot = sd["rotation"]
            info.rotation = abs(int(float(rot))) % 360 if rot is not None else 0
            if not info.duration:
                info.duration = float(s.get("duration") or 0.0)
        elif stype == "audio":
            info.has_audio = True
    info.created_at = tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time")
    info.location = tags.get("com.apple.quicktime.location.iso6709") or tags.get("location")
    info.device = " ".join(
        filter(None, [tags.get("com.apple.quicktime.make"), tags.get("com.apple.quicktime.model")])
    ) or tags.get("encoder")
    return info


def media_duration(path: Path) -> float:
    return probe(path).duration


def detect_scenes(path: Path, threshold: float = 0.3, analysis_fps: int = 6) -> list[float]:
    """Return scene-change timestamps (seconds). Decodes at low res/fps for speed."""
    proc = subprocess.run(
        [
            require("ffmpeg"),
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-an",
            "-vf",
            f"fps={analysis_fps},scale=160:-2,select='gt(scene,{threshold})',showinfo",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", proc.stderr)]


def contact_sheet(path: Path, out: Path, *, duration: float, cols: int = 4, rows: int = 3, width: int = 320) -> Path:
    n = cols * rows
    interval = max(duration / n, 0.04)
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(
        "-i",
        str(path),
        "-vf",
        f"fps=1/{interval:.4f},scale={width}:-2,"
        f"drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,"
        f"tile={cols}x{rows}",
        "-frames:v",
        "1",
        "-q:v",
        "4",
        str(out),
    )
    return out


def thumbnail(path: Path, out: Path, at: float, width: int = 480) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(
        "-ss", f"{max(at, 0):.3f}", "-i", str(path), "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "4", str(out)
    )
    return out


def loudness(path: Path) -> dict[str, float]:
    proc = subprocess.run(
        [
            require("ffmpeg"),
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-vn",
            "-af",
            "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", proc.stderr, re.S)
    if not m:
        return {}
    d = json.loads(m.group(0))
    return {"integrated_lufs": float(d["input_i"]), "true_peak_db": float(d["input_tp"]), "lra": float(d["input_lra"])}


def black_segments(path: Path, min_duration: float = 0.2) -> list[tuple[float, float]]:
    proc = subprocess.run(
        [
            require("ffmpeg"),
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-an",
            "-vf",
            f"blackdetect=d={min_duration}:pix_th=0.08",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", proc.stderr)]


def parse_created(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
