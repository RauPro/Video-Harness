"""Incrementally index footage folders (phone clips, Insta360 exports, photos) into the catalog."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .catalog import Catalog, clip_id_for
from .ffmpeg import FFmpegError, contact_sheet, detect_scenes, probe, thumbnail
from .paths import cache_dir

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".mts", ".m2ts", ".webm", ".3gp", ".insv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
SKIP_EXTS = {".lrv", ".thm", ".insp"}  # Insta360 low-res proxies / thumbnails / raw photos
MAX_SCENE_SCAN_SECONDS = 1800


def iter_media(roots: list[Path]) -> Iterator[Path]:
    for root in roots:
        root = Path(root).expanduser()
        if root.is_file():
            yield root
            continue
        for p in sorted(root.rglob("*")):
            if p.name.startswith(".") or p.name.startswith("._") or not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext in SKIP_EXTS:
                continue
            if ext in VIDEO_EXTS or ext in IMAGE_EXTS:
                yield p


def analyze_file(path: Path, *, scenes: bool = True) -> dict:
    st = path.stat()
    cid = clip_id_for(path)
    ext = path.suffix.lower()
    info = probe(path)
    kind = "image" if ext in IMAGE_EXTS else ("insv_raw" if ext == ".insv" else "video")
    out = cache_dir() / cid
    fields: dict = {
        "id": cid,
        "path": str(path.resolve()),
        "size": st.st_size,
        "mtime": st.st_mtime,
        "duration": info.duration if kind != "image" else 0.0,
        "width": info.display_size[0],
        "height": info.display_size[1],
        "fps": info.fps,
        "vcodec": info.vcodec,
        "rotation": info.rotation,
        "orientation": info.orientation,
        "has_audio": int(info.has_audio),
        "created_at": info.created_at,
        "location": info.location,
        "device": info.device,
        "kind": kind,
    }
    try:
        if kind == "image":
            fields["thumb"] = str(thumbnail(path, out / "thumb.jpg", 0))
        else:
            fields["thumb"] = str(thumbnail(path, out / "thumb.jpg", min(1.0, info.duration / 2)))
            fields["sheet"] = str(contact_sheet(path, out / "sheet.jpg", duration=info.duration))
            if scenes and info.duration <= MAX_SCENE_SCAN_SECONDS:
                fields["scenes"] = json.dumps([round(t, 2) for t in detect_scenes(path)])
    except FFmpegError as e:
        fields["description"] = f"[preview failed: {str(e).splitlines()[0][:120]}]"
    return fields


def ingest(
    roots: list[Path],
    *,
    catalog: Catalog,
    workers: int = 4,
    scenes: bool = True,
    force: bool = False,
    on_progress: Callable[[str, Path], None] | None = None,
) -> dict[str, int]:
    todo: list[Path] = []
    counts = {"seen": 0, "skipped": 0, "indexed": 0, "failed": 0}
    for p in iter_media(roots):
        counts["seen"] += 1
        st = p.stat()
        if not force and catalog.is_current(p.resolve(), st.st_size, st.st_mtime):
            counts["skipped"] += 1
            continue
        todo.append(p)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(analyze_file, p, scenes=scenes): p for p in todo}
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                fields = fut.result()
            except Exception as e:  # noqa: BLE001 - one bad file must not stop a 5 TB scan
                counts["failed"] += 1
                if on_progress:
                    on_progress(f"failed: {e}".splitlines()[0][:160], p)
                continue
            existing = catalog.get(fields["id"])
            if existing:  # keep human/agent annotations across re-index
                changed = (
                    existing.row["size"] != fields["size"] or abs((existing.row["mtime"] or 0) - fields["mtime"]) > 1e-3
                )
                keeps = (
                    ("description", "tags", "rating")
                    if changed
                    else ("description", "tags", "rating", "transcript", "words", "language")
                )
                if changed:  # new content: stale speech data must go so --transcribe redoes it
                    fields.update(transcript=None, words=None, language=None)
                for keep in keeps:
                    if existing.row[keep] and keep not in fields:
                        fields[keep] = existing.row[keep]
            catalog.upsert(fields)
            counts["indexed"] += 1
            if on_progress:
                on_progress("indexed", p)
    return counts
