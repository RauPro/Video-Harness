"""Resolve a project into Remotion input props and render it."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from .ffmpeg import FFmpegError, ffmpeg, loudness, media_duration
from .paths import RENDERER_DIR, SFX_DIR
from .sfx import LIBRARY
from .sfx import generate as generate_sfx
from .styles import load_theme
from .timeline import ImageInsert, Timeline, lint_timeline
from .transcribe import speech_regions


class RenderError(RuntimeError):
    pass


def _sfx_src(project: Path, name: str) -> str:
    if name in LIBRARY:
        dest = project / "sfx" / f"{name}.wav"
        if not dest.exists():
            generate_sfx(SFX_DIR)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SFX_DIR / f"{name}.wav", dest)
        return f"sfx/{name}.wav"
    if not (project / name).exists():
        raise RenderError(f"sfx {name!r} is neither a library sound ({', '.join(LIBRARY)}) nor a project file")
    return name


def resolve_props(tl: Timeline, project: Path) -> dict:
    missing = [c.id for c in tl.video if not c.src or not (project / c.src).exists()]
    if missing:
        raise RenderError(f"clips not conformed: {missing}; run `vh conform {project}` first")
    for ov in tl.overlays:
        if isinstance(ov, ImageInsert) and not (project / ov.src).exists():
            raise RenderError(f"imageInsert src not found in project: {ov.src}")
    theme = load_theme(tl.style)
    captions: list[dict] = []
    if tl.captions and (tl.captions.preset or theme["captions"]["preset"]) != "none":
        cap_path = project / tl.captions.src
        if not cap_path.exists():
            raise RenderError(f"{cap_path} missing; run `vh captions {project}`")
        captions = json.loads(cap_path.read_text())
        offset = round((tl.voiceover.start if tl.voiceover else 0) * 1000)
        if offset:
            captions = [{**c, "startMs": c["startMs"] + offset, "endMs": c["endMs"] + offset} for c in captions]
    sfx = [{**s.model_dump(), "src": _sfx_src(project, s.src)} for s in tl.sfx]
    for ov in tl.overlays:
        if ov.sfx:
            sfx.append({"src": _sfx_src(project, ov.sfx), "start": ov.start, "volume": 0.6})
    w, h = tl.size
    duration = tl.computed_duration()
    data = tl.model_dump(mode="json", exclude_none=True)
    data["sfx"] = sfx
    return {
        "timeline": data,
        "theme": theme,
        "captions": captions,
        "speech": speech_regions(captions),
        "width": w,
        "height": h,
        "fps": tl.fps,
        "durationInFrames": max(1, round(duration * tl.fps)),
    }


def _npx() -> list[str]:
    if not (RENDERER_DIR / "node_modules" / "remotion").exists():
        raise RenderError(f"renderer deps missing; run `vh setup` (npm install in {RENDERER_DIR})")
    npx = shutil.which("npx")
    if not npx:
        raise RenderError("npx not found; install Node.js 20+")
    return [npx, "--no-install", "remotion"]


def write_props(tl: Timeline, project: Path) -> Path:
    props = resolve_props(tl, project)
    path = project / "out" / "props.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(props))
    return path


def render(
    tl: Timeline,
    project: Path,
    out: Path,
    *,
    preview: bool = False,
    master: bool = True,
    concurrency: int | None = None,
) -> Path:
    for w in lint_timeline(tl):
        print(f"warning: {w}")
    props = write_props(tl, project)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_name(out.stem + ".raw.mp4") if master else out
    cmd = [
        *_npx(),
        "render",
        "src/index.ts",
        "Main",
        str(raw.resolve()),
        f"--props={props.resolve()}",
        f"--public-dir={project.resolve()}",
        "--codec=h264",
        "--audio-codec=aac",
        "--audio-bitrate=256k",
        f"--crf={23 if preview else 16}",
        "--log=error",
    ]
    if preview:
        cmd += ["--scale=0.5", "--jpeg-quality=70"]
    if concurrency:
        cmd.append(f"--concurrency={concurrency}")
    proc = subprocess.run(cmd, cwd=RENDERER_DIR, env={**os.environ, "BROWSER": "none"})
    if proc.returncode != 0:
        raise RenderError("remotion render failed (see output above)")
    if master:
        master_audio(raw, out)
        raw.unlink(missing_ok=True)
    return out


def master_audio(src: Path, out: Path, target: float = -14.0) -> Path:
    """Two-pass loudnorm to platform loudness (-14 LUFS, -1 dBTP); video stream is copied."""
    m = loudness(src)
    if not m or m["integrated_lufs"] < -60:
        shutil.copy2(src, out)
        return out
    af = (
        f"loudnorm=I={target}:TP=-1:LRA=11:measured_I={m['integrated_lufs']}:measured_TP={m['true_peak_db']}"
        f":measured_LRA={m['lra']}:linear=true"
    )
    try:
        ffmpeg(
            "-i",
            str(src),
            "-c:v",
            "copy",
            "-af",
            af,
            "-ar",
            "48000",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-movflags",
            "+faststart",
            str(out),
        )
    except FFmpegError:
        shutil.copy2(src, out)
    return out


def still(tl: Timeline, project: Path, at: float, out: Path) -> Path:
    props = write_props(tl, project)
    frame = min(round(at * tl.fps), round(tl.computed_duration() * tl.fps) - 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        *_npx(),
        "still",
        "src/index.ts",
        "Main",
        str(out.resolve()),
        f"--props={props.resolve()}",
        f"--public-dir={project.resolve()}",
        f"--frame={max(0, frame)}",
        "--log=error",
        "--scale=0.5",
    ]
    if subprocess.run(cmd, cwd=RENDERER_DIR).returncode != 0:
        raise RenderError("remotion still failed")
    return out


def voice_duration(tl: Timeline, project: Path) -> float | None:
    if tl.voiceover and (project / tl.voiceover.src).exists():
        return media_duration(project / tl.voiceover.src) + tl.voiceover.start
    return None
