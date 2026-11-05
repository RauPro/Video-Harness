"""SQLite footage catalog. Indexes files in place; never copies or modifies originals."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .paths import catalog_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS clips (
  id TEXT PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  size INTEGER, mtime REAL,
  duration REAL, width INTEGER, height INTEGER, fps REAL, vcodec TEXT, rotation INTEGER,
  orientation TEXT, has_audio INTEGER, created_at TEXT, location TEXT, device TEXT,
  kind TEXT,                 -- video | image | insv_raw
  sheet TEXT, thumb TEXT,
  scenes TEXT,               -- JSON list of scene-change seconds
  transcript TEXT, words TEXT, language TEXT,
  description TEXT, tags TEXT, rating INTEGER,
  indexed_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE VIRTUAL TABLE IF NOT EXISTS clips_fts USING fts5(
  id UNINDEXED, path, transcript, description, tags, location, device, tokenize='unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS usage (
  clip_id TEXT NOT NULL, project TEXT NOT NULL, source_in REAL NOT NULL, duration REAL,
  published INTEGER DEFAULT 0, used_at TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (clip_id, project, source_in)
);
"""

FTS_FIELDS = ("path", "transcript", "description", "tags", "location", "device")


def clip_id_for(path: Path) -> str:
    return "c_" + hashlib.sha1(str(Path(path).resolve()).encode()).hexdigest()[:10]


@dataclass
class Clip:
    row: sqlite3.Row

    def __getattr__(self, name: str):
        try:
            return self.row[name]
        except IndexError as e:
            raise AttributeError(name) from e

    def to_dict(self) -> dict:
        d = dict(self.row)
        for k in ("scenes", "words"):
            if d.get(k):
                d[k] = json.loads(d[k])
        return d


class Catalog:
    def __init__(self, path: Path | None = None):
        self.path = Path(path or catalog_path())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        with self.db:
            yield self.db

    def is_current(self, path: Path, size: int, mtime: float) -> bool:
        r = self.db.execute("SELECT size, mtime FROM clips WHERE path=?", (str(path),)).fetchone()
        return bool(r) and r["size"] == size and abs((r["mtime"] or 0) - mtime) < 1e-3

    def upsert(self, fields: dict) -> None:
        cols = list(fields)
        sql = (
            f"INSERT INTO clips ({','.join(cols)}) VALUES ({','.join('?' * len(cols))}) "
            f"ON CONFLICT(id) DO UPDATE SET {','.join(f'{c}=excluded.{c}' for c in cols if c != 'id')}"
        )
        with self.tx() as db:
            db.execute(sql, [fields[c] for c in cols])
        self._reindex(fields["id"])

    def update(self, clip_id: str, **fields) -> None:
        if not fields:
            return
        sets = ",".join(f"{k}=?" for k in fields)
        with self.tx() as db:
            cur = db.execute(f"UPDATE clips SET {sets} WHERE id=?", [*fields.values(), clip_id])
            if cur.rowcount == 0:
                raise KeyError(clip_id)
        self._reindex(clip_id)

    def _reindex(self, clip_id: str) -> None:
        r = self.db.execute(f"SELECT id,{','.join(FTS_FIELDS)} FROM clips WHERE id=?", (clip_id,)).fetchone()
        with self.tx() as db:
            db.execute("DELETE FROM clips_fts WHERE id=?", (clip_id,))
            if r:
                db.execute(
                    f"INSERT INTO clips_fts (id,{','.join(FTS_FIELDS)}) VALUES (?{',?' * len(FTS_FIELDS)})",
                    [r["id"], *[r[f] or "" for f in FTS_FIELDS]],
                )

    def get(self, clip_id: str) -> Clip | None:
        r = self.db.execute("SELECT * FROM clips WHERE id=?", (clip_id,)).fetchone()
        return Clip(r) if r else None

    def resolve(self, source: str) -> Path:
        """Turn a timeline `source` (catalog id or path) into a file path."""
        if source.startswith("c_"):
            c = self.get(source)
            if not c:
                raise KeyError(f"clip {source} not in catalog {self.path}")
            return Path(c.path)
        return Path(source).expanduser()

    def remove_missing(self) -> int:
        gone = [r["id"] for r in self.db.execute("SELECT id, path FROM clips") if not Path(r["path"]).exists()]
        with self.tx() as db:
            db.executemany("DELETE FROM clips WHERE id=?", [(i,) for i in gone])
            db.executemany("DELETE FROM clips_fts WHERE id=?", [(i,) for i in gone])
            db.executemany("DELETE FROM usage WHERE clip_id=?", [(i,) for i in gone])
        return len(gone)

    def search(
        self,
        query: str | None = None,
        *,
        orientation: str | None = None,
        min_duration: float | None = None,
        max_duration: float | None = None,
        has_speech: bool | None = None,
        undescribed: bool = False,
        unused: bool = False,
        after: str | None = None,
        before: str | None = None,
        path_like: str | None = None,
        limit: int = 30,
    ) -> list[Clip]:
        where, args = [], []
        if query:
            where.append("c.id IN (SELECT id FROM clips_fts WHERE clips_fts MATCH ?)")
            args.append(_fts_query(query))
        if orientation:
            where.append("c.orientation=?")
            args.append(orientation)
        if min_duration is not None:
            where.append("c.duration>=?")
            args.append(min_duration)
        if max_duration is not None:
            where.append("c.duration<=?")
            args.append(max_duration)
        if has_speech is True:
            where.append("length(coalesce(c.transcript,''))>20")
        elif has_speech is False:
            where.append("length(coalesce(c.transcript,''))<=20")
        if undescribed:
            where.append("coalesce(c.description,'')=''")
        if unused:
            where.append("c.id NOT IN (SELECT clip_id FROM usage)")
        if after:
            where.append("c.created_at>=?")
            args.append(after)
        if before:
            where.append("c.created_at<=?")
            args.append(before)
        if path_like:
            where.append("c.path LIKE ?")
            args.append(f"%{path_like}%")
        sql = "SELECT c.* FROM clips c"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY coalesce(c.rating,0) DESC, c.created_at DESC LIMIT ?"
        args.append(limit)
        return [Clip(r) for r in self.db.execute(sql, args)]

    def stats(self) -> dict:
        r = self.db.execute(
            "SELECT count(*) n, sum(duration) secs, sum(size) bytes, "
            "sum(coalesce(description,'')<>'') described, sum(coalesce(transcript,'')<>'') transcribed FROM clips"
        ).fetchone()
        by = self.db.execute("SELECT orientation, count(*) n FROM clips GROUP BY orientation").fetchall()
        return {**dict(r), "by_orientation": {b["orientation"]: b["n"] for b in by}}

    def record_usage(self, project: Path, uses: Iterable[tuple[str, float, float]]) -> int:
        """Replace the clips recorded for `project` with (clip_id, source_in, duration) rows."""
        key = str(Path(project).resolve())
        rows = [(cid, key, round(t, 3), round(d, 3)) for cid, t, d in uses if self.get(cid)]
        with self.tx() as db:
            prev = db.execute("SELECT max(published) p FROM usage WHERE project=?", (key,)).fetchone()["p"] or 0
            db.execute("DELETE FROM usage WHERE project=?", (key,))
            db.executemany(
                "INSERT OR REPLACE INTO usage (clip_id, project, source_in, duration, published) VALUES (?,?,?,?,?)",
                [(*r, prev) for r in rows],
            )
        return len(rows)

    def mark_published(self, project: Path) -> None:
        with self.tx() as db:
            db.execute("UPDATE usage SET published=1 WHERE project=?", (str(Path(project).resolve()),))

    def usage(self, clip_id: str | None = None) -> list[dict]:
        sql, args = "SELECT * FROM usage", []
        if clip_id:
            sql, args = sql + " WHERE clip_id=?", [clip_id]
        return [dict(r) for r in self.db.execute(sql + " ORDER BY used_at, project, source_in", args)]

    def find_id(self, source: str, project: Path | None = None) -> str | None:
        """Catalog id for a timeline `source` (an id or a file path), if the file is catalogued."""
        if source.startswith("c_"):
            return source if self.get(source) else None
        p = Path(source).expanduser()
        if not p.is_absolute() and project is not None:
            p = Path(project) / p
        cid = clip_id_for(p)
        return cid if self.get(cid) else None

    def all_ids(self) -> Iterable[str]:
        return [r["id"] for r in self.db.execute("SELECT id FROM clips")]


def _fts_query(q: str) -> str:
    """Quote each term so user text can't break FTS syntax; terms are ANDed, prefix-matched."""
    terms = [t.replace('"', "") for t in q.split() if t.strip('"')]
    return " ".join(f'"{t}"*' for t in terms) or '""'
