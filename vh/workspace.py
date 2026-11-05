"""The user's video workspace: a fixed folder layout for footage, reusable assets, projects, published videos and
ideas. Lives outside the repo (default ~/VideoHarness, override with VH_WORKSPACE)."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

from .paths import workspace_dir

LAYOUT = (
    "footage/phone",
    "footage/insta360",
    "assets/music",
    "assets/sfx",
    "assets/images",
    "assets/brand",
    "projects",
    "published",
    "ideas",
)
ASSET_KINDS = ("music", "sfx", "images", "brand")
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif"}
VIDEO_EXTS = {".mp4", ".mov", ".webm"}
ASSETS_JSON = "assets/assets.json"
README = """# Video workspace (managed by vh)

footage/phone, footage/insta360   Raw footage you want kept here (optional: `vh ingest` indexes any folder in place)
assets/music                      Tracks you have the rights to. Tag them: vh assets tag <file> --mood --license
assets/sfx                        Your own sound effects (the built-in library is always available)
assets/images                     Photos, screenshots, maps, logos for imageInsert overlays
assets/brand                      Intro/outro, watermark, fonts
projects/<date>-<slug>            One folder per video (vh new <slug>)
published/<date>-<slug>           Final videos + meta.json (platform, url, views, clips used): vh publish
ideas/<slug>.md                   Video ideas proposed from the catalog (video-ideas skill)
"""


def root(path: Path | None = None) -> Path:
    return Path(path or workspace_dir()).expanduser()


def init_workspace(path: Path | None = None) -> Path:
    r = root(path)
    for d in LAYOUT:
        (r / d).mkdir(parents=True, exist_ok=True)
    if not (r / "README.md").exists():
        (r / "README.md").write_text(README)
    if not (r / ASSETS_JSON).exists():
        (r / ASSETS_JSON).write_text("{}\n")
    return r


def is_workspace(path: Path | None = None) -> bool:
    r = root(path)
    return (r / "projects").is_dir() and (r / "assets").is_dir()


def project_path(slug: str, path: Path | None = None, today: date | None = None) -> Path:
    return root(path) / "projects" / f"{(today or date.today()).isoformat()}-{slug}"


# ---------------------------------------------------------------- assets
def _asset_meta(r: Path) -> dict:
    p = r / ASSETS_JSON
    return json.loads(p.read_text()) if p.exists() else {}


def _rel(r: Path, file: Path) -> str:
    file = Path(file).expanduser()
    file = file if file.is_absolute() else (r / file)
    try:
        return file.resolve().relative_to((r / "assets").resolve()).as_posix()
    except ValueError as e:
        raise ValueError(f"{file} is not inside {r / 'assets'}") from e


def list_assets(kind: str | None = None, query: str | None = None, path: Path | None = None) -> list[dict]:
    r = root(path)
    meta = _asset_meta(r)
    out = []
    for k in [kind] if kind else ASSET_KINDS:
        base = r / "assets" / k
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*")):
            if not f.is_file() or f.name.startswith("."):
                continue
            ext = f.suffix.lower()
            if ext not in AUDIO_EXTS | IMAGE_EXTS | VIDEO_EXTS:
                continue
            rel = f.relative_to(r / "assets").as_posix()
            item = {"asset": rel, "kind": k, "path": str(f), **meta.get(rel, {})}
            if ext in AUDIO_EXTS | VIDEO_EXTS and "duration" not in item:
                item["duration"] = _duration(f)
            hay = " ".join(str(v) for v in item.values()).lower()
            if query and not all(t in hay for t in query.lower().split()):
                continue
            out.append(item)
    return out


def _duration(f: Path) -> float | None:
    try:
        from .ffmpeg import media_duration

        return round(media_duration(f), 2)
    except Exception:
        return None


def tag_asset(file: Path, path: Path | None = None, **fields: str | None) -> dict:
    r = root(path)
    rel = _rel(r, file)
    if not (r / "assets" / rel).exists():
        raise FileNotFoundError(r / "assets" / rel)
    meta = _asset_meta(r)
    entry = meta.setdefault(rel, {})
    entry.update({k: v for k, v in fields.items() if v is not None})
    (r / ASSETS_JSON).write_text(json.dumps(meta, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    return entry


def use_asset(project: Path, file: Path, path: Path | None = None) -> str:
    """Copy a workspace asset into the project (renders only read project files). Returns the project-relative src."""
    r = root(path)
    rel = _rel(r, file)
    src = r / "assets" / rel
    if not src.exists():
        raise FileNotFoundError(src)
    sub = {"music": "music", "sfx": "sfx"}.get(rel.split("/", 1)[0], "media/assets")
    dest = project / sub / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dest)
    return dest.relative_to(project).as_posix()


# ---------------------------------------------------------------- published
def publish(
    project: Path,
    *,
    platform: str,
    url: str | None = None,
    title: str | None = None,
    clips: list[str] | None = None,
    path: Path | None = None,
    today: date | None = None,
) -> Path:
    final = project / "out" / "final.mp4"
    if not final.exists():
        raise FileNotFoundError(f"{final} not found; run vh build first")
    r = root(path)
    key = str(project.resolve())
    prev = [m.parent for m in (r / "published").glob("*/meta.json") if json.loads(m.read_text()).get("project") == key]
    name = project.name if project.name[:4].isdigit() else f"{(today or date.today()).isoformat()}-{project.name}"
    dest = prev[0] if prev else r / "published" / name
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(final, dest / "final.mp4")
    for extra in ("script.md", "timeline.json"):
        if (project / extra).exists():
            shutil.copy2(project / extra, dest / extra)
    meta_path = dest / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"posts": []}
    meta.update(
        {
            "title": title or meta.get("title") or project.name,
            "project": key,
            "clips": clips if clips is not None else meta.get("clips", []),
        }
    )
    posts = [p for p in meta["posts"] if p["platform"] != platform]
    posts.append({"platform": platform, "url": url, "publishedAt": (today or date.today()).isoformat(), "views": None})
    meta["posts"] = posts
    meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")
    return dest


def list_published(path: Path | None = None) -> list[dict]:
    r = root(path)
    out = []
    for m in sorted((r / "published").glob("*/meta.json")):
        out.append({"folder": m.parent.name, **json.loads(m.read_text())})
    return out


def refresh_views(path: Path | None = None) -> int:
    """Update view counts of published posts with a URL (needs yt-dlp)."""
    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        raise RuntimeError("yt-dlp not installed: uv sync --extra download")
    n = 0
    for m in sorted((root(path) / "published").glob("*/meta.json")):
        meta = json.loads(m.read_text())
        for p in meta.get("posts", []):
            if not p.get("url"):
                continue
            r = subprocess.run([ytdlp, "-J", "--skip-download", p["url"]], capture_output=True, text=True)
            if r.returncode == 0 and r.stdout:
                info = json.loads(r.stdout)
                p.update({k: info.get(k) for k in ("view_count", "like_count", "comment_count") if info.get(k)})
                p["views"] = info.get("view_count")
                n += 1
        m.write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")
    return n
