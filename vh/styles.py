from __future__ import annotations

import json

from .paths import STYLES_DIR


def list_styles() -> list[str]:
    return sorted(p.parent.name for p in STYLES_DIR.glob("*/theme.json"))


def load_theme(name: str) -> dict:
    path = STYLES_DIR / name / "theme.json"
    if not path.exists():
        raise KeyError(f"unknown style {name!r}; available: {', '.join(list_styles())}")
    theme = json.loads(path.read_text())
    base = theme.pop("extends", None)
    if base:
        merged = load_theme(base)
        for k, v in theme.items():
            merged[k] = {**merged.get(k, {}), **v} if isinstance(v, dict) else v
        return merged
    return theme
