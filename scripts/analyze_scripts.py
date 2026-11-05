"""Transcribe a channel's most-viewed videos and print script metrics (speech rate, numbers, opening line).

    uv sync --extra download
    uv run python scripts/analyze_scripts.py https://www.tiktok.com/@raul.guillen.h --top 8 --out /tmp/raul

Writes <out>/<id>.json transcripts and <out>/metrics.json. Long videos are cut to the first --max-seconds.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from vh.transcribe import plain_text, transcribe


def top_videos(url: str, n: int, scan: int) -> list[dict]:
    raw = subprocess.run(
        [shutil.which("yt-dlp") or "yt-dlp", "--flat-playlist", "--playlist-end", str(scan), "-J", url],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    entries = [e for e in json.loads(raw).get("entries", []) if e.get("view_count")]
    return sorted(entries, key=lambda e: -e["view_count"])[:n]


def download(entry: dict, out: Path, max_seconds: int) -> Path:
    dest = out / f"{entry['id']}.mp3"
    if not dest.exists():
        url = entry.get("url") or entry.get("webpage_url") or entry["id"]
        cmd = ["yt-dlp", "-f", "ba/b", "-x", "--audio-format", "mp3", "-q", "--no-playlist"]
        cmd += ["--download-sections", f"*0-{max_seconds}", "-o", str(out / f"{entry['id']}.%(ext)s"), url]
        subprocess.run(cmd, check=True)
    return dest


def metrics(words: list[dict]) -> dict:
    text = plain_text(words)
    span = max((words[-1]["endMs"] - words[0]["startMs"]) / 1000, 1)
    return {
        "words": len(words),
        "wpm": round(len(words) / span * 60),
        "firstWordAt": round(words[0]["startMs"] / 1000, 2),
        "numbersPerMin": round(len(re.findall(r"\$|\d+|dólar|dollar|baht|precio|price", text, re.I)) / span * 60, 1),
        "questionsPerMin": round(text.count("?") / span * 60, 1),
        "opening": "".join(w["text"] for w in words if w["startMs"] < words[0]["startMs"] + 3000).strip(),
        "ending": "".join(w["text"] for w in words if w["startMs"] > words[-1]["endMs"] - 12000).strip(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="Channel/profile URL, e.g. https://www.youtube.com/@ericstruk/shorts")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--scan", type=int, default=150, help="How many recent uploads to rank by views.")
    ap.add_argument("--max-seconds", type=int, default=240)
    ap.add_argument("--model", default="small")
    ap.add_argument("--out", type=Path, default=Path("references/scripts"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for e in top_videos(a.url, a.top, a.scan):
        words, lang = transcribe(download(e, a.out, a.max_seconds), model=a.model)
        if not words:
            continue
        (a.out / f"{e['id']}.json").write_text(json.dumps({"language": lang, "words": words}, ensure_ascii=False))
        row = {"id": e["id"], "title": e.get("title"), "views": e["view_count"], "language": lang, **metrics(words)}
        rows.append(row)
        print(f"{row['views']:>12,}  {row['wpm']:>3} wpm  {row['opening']}")
    (a.out / "metrics.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
