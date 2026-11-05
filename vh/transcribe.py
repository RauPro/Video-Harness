"""Speech-to-text with word timestamps (faster-whisper) and script alignment.

Captions use Remotion's `Caption` shape: {text, startMs, endMs, timestampMs, confidence}.
Word texts after the first carry a leading space, as `createTikTokStyleCaptions` expects.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

Caption = dict


@lru_cache(maxsize=2)
def _model(name: str):
    from faster_whisper import WhisperModel

    return WhisperModel(name, device="auto", compute_type="int8")


def transcribe(path: Path, *, model: str = "small", language: str | None = None) -> tuple[list[Caption], str]:
    segments, info = _model(model).transcribe(
        str(path), language=language, word_timestamps=True, vad_filter=True, beam_size=5
    )
    words: list[Caption] = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if not text:
                continue
            words.append(
                {
                    "text": text,
                    "startMs": round(w.start * 1000),
                    "endMs": round(w.end * 1000),
                    "timestampMs": round((w.start + w.end) * 500),
                    "confidence": round(float(w.probability), 3),
                }
            )
    return with_spacing(words), info.language


def with_spacing(words: list[Caption]) -> list[Caption]:
    out = []
    for i, w in enumerate(words):
        t = w["text"].strip()
        out.append({**w, "text": t if i == 0 else " " + t})
    return out


def plain_text(words: list[Caption]) -> str:
    return "".join(w["text"] for w in words).strip()


_DIRECTION = re.compile(r"\[[^\]]*\]|\([^)]*\bB-?ROLL\b[^)]*\)|<!--.*?-->", re.S | re.I)


def narration_from_script(script: str) -> str:
    """Spoken text from a script.md: drops headings, [directions], > notes, and HTML comments."""
    lines = []
    for line in _DIRECTION.sub("", script).splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("---"):
            continue
        lines.append(s.lstrip("-* ").strip())
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _norm(token: str) -> str:
    t = unicodedata.normalize("NFKD", token.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^\w$%]+", "", t)


def align_to_script(words: list[Caption], script_text: str) -> list[Caption]:
    """Keep whisper timings, but use the script's spelling/punctuation for caption text."""
    tokens = script_text.split()
    if not words or not tokens:
        return words
    a = [_norm(w["text"]) for w in words]
    b = [_norm(t) for t in tokens]
    out: list[Caption] = []
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                out.append({**words[i1 + k], "text": tokens[j1 + k]})
        elif op == "delete":
            continue  # whisper heard something that's not in the script (filler); drop it
        else:  # replace / insert: spread script tokens across the available time span
            if i2 > i1:
                start, end = words[i1]["startMs"], words[i2 - 1]["endMs"]
            else:
                start = out[-1]["endMs"] if out else 0
                end = words[i1]["startMs"] if i1 < len(words) else start + 300 * (j2 - j1)
                end = max(end, start + 120 * (j2 - j1))
            n = j2 - j1
            for k in range(n):
                s = start + (end - start) * k / n
                e = start + (end - start) * (k + 1) / n
                out.append(
                    {
                        "text": tokens[j1 + k],
                        "startMs": round(s),
                        "endMs": round(e),
                        "timestampMs": round((s + e) / 2),
                        "confidence": None,
                    }
                )
    return with_spacing(out)


def speech_regions(words: list[Caption], max_gap_ms: int = 600, pad_ms: int = 120) -> list[list[int]]:
    regions: list[list[int]] = []
    for w in words:
        s, e = w["startMs"] - pad_ms, w["endMs"] + pad_ms
        if regions and s - regions[-1][1] <= max_gap_ms:
            regions[-1][1] = max(regions[-1][1], e)
        else:
            regions.append([max(0, s), e])
    return regions


def phrases(words: list[Caption], pause_ms: int = 350, max_words: int = 14) -> list[dict]:
    """Split captions into phrases (natural cut points) by punctuation and pauses."""
    out: list[dict] = []
    cur: list[Caption] = []

    def flush() -> None:
        if cur:
            out.append(
                {
                    "start": cur[0]["startMs"] / 1000,
                    "end": cur[-1]["endMs"] / 1000,
                    "text": plain_text(with_spacing(cur)),
                }
            )
            cur.clear()

    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        ends_sentence = w["text"].strip()[-1:] in ".!?;:,…"
        pause = nxt is not None and nxt["startMs"] - w["endMs"] >= pause_ms
        if nxt is None or ends_sentence or pause or len(cur) >= max_words:
            flush()
    return out
