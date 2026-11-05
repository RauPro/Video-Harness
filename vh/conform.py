"""Conform: cut each chosen shot (+ handles) from the original, reframe/crop to the output format,
and normalize codecs (HEVC/10-bit/VFR phone footage -> H.264 yuv420p CFR) so the renderer is fast
and deterministic. Originals are never modified."""

from __future__ import annotations

import hashlib
import math
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .catalog import Catalog
from .ffmpeg import FFmpegError, ffmpeg, probe
from .ingest import IMAGE_EXTS
from .timeline import ImageInsert, Timeline, VideoClip

HANDLE = 0.25


def _even(n: float) -> int:
    return int(round(n / 2) * 2)


def build_filter(clip: VideoClip, w: int, h: int, fps: int, src_w: int, src_h: int) -> str:
    chain: list[str] = []
    if clip.reframe:
        r = clip.reframe
        long_fov = r.fov
        if w >= h:
            h_fov = long_fov
            v_fov = math.degrees(2 * math.atan(math.tan(math.radians(h_fov / 2)) * h / w))
        else:
            v_fov = long_fov
            h_fov = math.degrees(2 * math.atan(math.tan(math.radians(v_fov / 2)) * w / h))
        chain.append(
            f"v360=input=e:output=flat:yaw={r.yaw}:pitch={r.pitch}:roll={r.roll}"
            f":h_fov={h_fov:.2f}:v_fov={v_fov:.2f}:w={w}:h={h}:interp=cubic"
        )
    if clip.speed != 1:
        chain.append(f"setpts=PTS/{clip.speed}")
    fx = clip.zoom.focusX if clip.zoom else 0.5
    fy = clip.zoom.focusY if clip.zoom else 0.5
    if clip.fit == "cover" or clip.reframe:
        chain.append(f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos")
        chain.append(f"crop={w}:{h}:(iw-{w})*{fx}:(ih-{h})*{fy}")
        vf = ",".join(chain)
    elif clip.fit == "contain":
        chain.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos")
        chain.append(f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black")
        vf = ",".join(chain)
    else:  # blur: sharp contained shot over a blurred, filled copy (horizontal clip in a vertical video)
        pre = ",".join(chain) + "," if chain else ""
        vf = (
            f"{pre}split=2[bg][fg];"
            f"[bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=40:2,eq=brightness=-0.08[b];"
            f"[fg]scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos[f];"
            f"[b][f]overlay=(W-w)/2:(H-h)/2"
        )
    return f"{vf},fps={fps},format=yuv420p,setsar=1"


def conform_clip(tl: Timeline, clip: VideoClip, project: Path, catalog: Catalog, force: bool = False) -> VideoClip:
    src = catalog.resolve(clip.source)
    if not src.is_absolute():
        src = (project / src).resolve()
    if not src.exists():
        raise FileNotFoundError(f"{clip.id}: source not found: {src}")
    if src.suffix.lower() == ".insv":
        raise FFmpegError(
            f"{clip.id}: {src.name} is a raw Insta360 file. Export it from Insta360 Studio as a 360 MP4 "
            "(equirectangular) and ingest that, then use `reframe` in the timeline."
        )
    w, h = tl.size
    is_image = clip.kind == "image" or src.suffix.lower() in IMAGE_EXTS
    st = src.stat()
    handle_in = 0.0 if is_image else min(HANDLE, clip.sourceIn)
    length = clip.duration * clip.speed + handle_in + HANDLE
    info = probe(src)
    vf = build_filter(clip, w, h, tl.fps, *info.display_size)
    key = hashlib.sha1(
        f"{src}|{st.st_size}|{st.st_mtime}|{clip.sourceIn}|{length}|{vf}|{is_image}".encode()
    ).hexdigest()[:10]
    rel = Path("media") / f"{clip.id}-{key}.mp4"
    out = project / rel
    if force or not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp.mp4")
        if is_image:
            inputs = ["-loop", "1", "-t", f"{length:.3f}", "-i", str(src)]
        else:
            inputs = ["-ss", f"{clip.sourceIn - handle_in:.3f}", "-t", f"{length:.3f}", "-i", str(src)]
        if is_image or not info.has_audio:
            inputs += ["-f", "lavfi", "-t", f"{length:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        afilter = [] if clip.speed == 1 or is_image or not info.has_audio else ["-af", _atempo(clip.speed)]
        vf_args = ["-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]"] if ";" in vf else ["-vf", vf, "-map", "0:v:0"]
        amap = ["-map", "1:a:0"] if (is_image or not info.has_audio) else ["-map", "0:a:0"]
        ffmpeg(
            *inputs,
            *vf_args,
            *amap,
            *afilter,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "17",
            "-g",
            str(tl.fps),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-t",
            f"{clip.duration + (handle_in + HANDLE) / clip.speed:.3f}",
            "-movflags",
            "+faststart",
            str(tmp),
        )
        tmp.replace(out)
    clip.src = rel.as_posix()
    clip.srcIn = round(handle_in / clip.speed, 4)
    return clip


def _atempo(speed: float) -> str:
    parts, s = [], speed
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append(f"atempo={s:.4f}")
    return ",".join(parts)


def conform_insert(ov: ImageInsert, project: Path, catalog: Catalog) -> None:
    if (
        not ov.src.startswith("c_")
        and not Path(ov.src).is_absolute()
        and (project / ov.src).exists()
        and not ov.src.startswith("..")
    ):
        return
    src = catalog.resolve(ov.src)
    if not src.is_absolute():
        src = (project / src).resolve()
    dest = project / "media" / f"insert-{hashlib.sha1(str(src).encode()).hexdigest()[:8]}{src.suffix.lower()}"
    if src.suffix.lower() in IMAGE_EXTS - {".heic"}:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(src, dest)
    else:
        dest = dest.with_suffix(".mp4")
        if not dest.exists():
            ffmpeg(
                "-i",
                str(src),
                "-t",
                f"{ov.duration + 0.5:.3f}",
                "-vf",
                "scale=1080:-2,fps=30,format=yuv420p",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                str(dest),
            )
    ov.src = dest.relative_to(project).as_posix()


def conform(tl: Timeline, project: Path, catalog: Catalog, *, workers: int = 3, force: bool = False) -> Timeline:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda c: conform_clip(tl, c, project, catalog, force), tl.video))
    for ov in tl.overlays:
        if isinstance(ov, ImageInsert):
            conform_insert(ov, project, catalog)
    return tl
