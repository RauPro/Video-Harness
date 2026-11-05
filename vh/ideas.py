"""Group the footage catalog into trips/shoots so an agent can propose videos from what was actually filmed."""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from .catalog import Catalog, Clip

_ISO6709 = re.compile(r"([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)")


def parse_location(loc: str | None) -> tuple[float, float] | None:
    m = _ISO6709.match(loc or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def _when(c: Clip) -> datetime | None:
    try:
        return datetime.fromisoformat((c.created_at or "").replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def group_shoots(clips: list[Clip], *, gap_days: float = 2, max_km: float = 150) -> list[list[Clip]]:
    """Split clips into shoots: a new shoot starts after a `gap_days` pause or a jump of more than `max_km`.
    Clips without a date are grouped by folder."""
    dated = sorted((c for c in clips if _when(c)), key=_when)
    groups: list[list[Clip]] = []
    last_t, last_loc = None, None
    for c in dated:
        t, loc = _when(c), parse_location(c.location)
        far = loc and last_loc and km(loc, last_loc) > max_km
        if not groups or (t - last_t).total_seconds() > gap_days * 86400 or far:
            groups.append([])
        groups[-1].append(c)
        last_t, last_loc = t, loc or last_loc
    by_folder: dict[str, list[Clip]] = {}
    for c in clips:
        if not _when(c):
            by_folder.setdefault(str(Path(c.path).parent), []).append(c)
    return groups + list(by_folder.values())


def summarize(group: list[Clip], used: set[str], *, samples: int = 6) -> dict:
    times = [t for t in map(_when, group) if t]
    locs = [p for p in (parse_location(c.location) for c in group) if p]
    tags = Counter(t.strip() for c in group for t in (c.tags or "").split(",") if t.strip())
    folders = Counter(str(Path(c.path).parent) for c in group)
    speech = [c for c in group if len(c.transcript or "") > 20]
    best = sorted(group, key=lambda c: (-(c.rating or 0), c.id in used, -(c.duration or 0)))[:samples]
    start = times[0].date().isoformat() if times else None
    return {
        "id": f"shoot-{start or Path(next(iter(folders))).name}",
        "start": start,
        "end": times[-1].date().isoformat() if times else None,
        "location": f"{sum(a for a, _ in locs) / len(locs):+.4f}{sum(b for _, b in locs) / len(locs):+.4f}"
        if locs
        else None,
        "clips": len(group),
        "minutes": round(sum(c.duration or 0 for c in group) / 60, 1),
        "unused": sum(c.id not in used for c in group),
        "described": sum(bool(c.description) for c in group),
        "orientation": dict(Counter(c.orientation or "?" for c in group)),
        "withSpeech": len(speech),
        "folders": [f for f, _ in folders.most_common(3)],
        "tags": [t for t, _ in tags.most_common(12)],
        "highlights": [
            {
                "id": c.id,
                "duration": round(c.duration or 0, 1),
                "orientation": c.orientation,
                "rating": c.rating,
                "used": c.id in used,
                "description": c.description,
                "sheet": c.sheet,
            }
            for c in best
        ],
        "speech": [{"id": c.id, "text": (c.transcript or "")[:160]} for c in speech[:samples]],
    }


def shoots(
    catalog: Catalog,
    *,
    gap_days: float = 2,
    max_km: float = 150,
    unused_only: bool = False,
    path_like: str | None = None,
    after: str | None = None,
    min_clips: int = 3,
) -> list[dict]:
    clips = catalog.search(path_like=path_like, after=after, unused=unused_only, limit=10**7)
    clips = [c for c in clips if c.kind != "image"]
    used = {u["clip_id"] for u in catalog.usage()}
    out = [summarize(g, used) for g in group_shoots(clips, gap_days=gap_days, max_km=max_km) if len(g) >= min_clips]
    return sorted(out, key=lambda s: (-s["unused"], s["start"] or ""))
