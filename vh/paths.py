from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(os.environ.get("VH_HOME", Path(__file__).resolve().parents[1]))
RENDERER_DIR = REPO_ROOT / "renderer"
STYLES_DIR = REPO_ROOT / "styles"
ASSETS_DIR = REPO_ROOT / "assets"
SFX_DIR = ASSETS_DIR / "sfx"
SCHEMA_PATH = REPO_ROOT / "schemas" / "timeline.schema.json"


def data_dir() -> Path:
    d = Path(os.environ.get("VH_DATA", Path.home() / ".vh"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def catalog_path() -> Path:
    return Path(os.environ.get("VH_CATALOG", data_dir() / "catalog.db"))


def cache_dir() -> Path:
    d = Path(os.environ.get("VH_CACHE", data_dir() / "cache"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def workspace_dir() -> Path:
    """Root of the user's video workspace (footage/, assets/, projects/, published/, ideas/)."""
    return Path(os.environ.get("VH_WORKSPACE", Path.home() / "VideoHarness")).expanduser()
