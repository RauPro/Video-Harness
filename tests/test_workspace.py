import json
from datetime import date

import pytest
from conftest import make_clip, needs_ffmpeg
from typer.testing import CliRunner

from vh.catalog import Catalog, clip_id_for
from vh.cli import app
from vh.ideas import group_shoots, parse_location, shoots
from vh.workspace import init_workspace, list_assets, list_published, publish, tag_asset, use_asset

runner = CliRunner()


@pytest.fixture
def ws(tmp_path, monkeypatch):
    root = tmp_path / "ws"
    monkeypatch.setenv("VH_WORKSPACE", str(root))
    return init_workspace()


def _add(cat: Catalog, path: str, created: str | None, loc: str | None = None, **kw) -> str:
    cid = clip_id_for(path)
    cat.upsert(
        {"id": cid, "path": path, "duration": 5.0, "created_at": created, "location": loc, "kind": "video", **kw}
    )
    return cid


def test_init_and_assets(ws, tmp_path):
    assert (ws / "assets" / "music").is_dir() and (ws / "published").is_dir() and (ws / "ideas").is_dir()
    track = ws / "assets" / "music" / "chill.mp3"
    track.write_bytes(b"fake")
    tag_asset(track, mood="chill", license="Epidemic Sound", tags="lofi,cafe")
    found = list_assets("music", "lofi")
    assert [a["asset"] for a in found] == ["music/chill.mp3"] and found[0]["license"] == "Epidemic Sound"
    assert list_assets(query="epic") == []

    project = tmp_path / "p"
    assert use_asset(project, track) == "music/chill.mp3"
    track.write_bytes(b"edit")
    use_asset(project, track)
    assert (project / "music" / "chill.mp3").read_bytes() == b"edit"
    for kind in ("images", "brand"):
        (ws / "assets" / kind / "logo.png").write_bytes(kind.encode())
    a, b = use_asset(project, ws / "assets/images/logo.png"), use_asset(project, ws / "assets/brand/logo.png")
    assert a != b and (project / a).read_bytes() == b"images"
    with pytest.raises(ValueError):
        tag_asset(tmp_path / "elsewhere.mp3")


def test_new_bare_name_goes_to_workspace(ws):
    r = runner.invoke(app, ["new", "bangkok-food"])
    assert r.exit_code == 0, r.output
    (proj,) = (ws / "projects").iterdir()
    assert proj.name.endswith("-bangkok-food") and proj.name[:10] == date.today().isoformat()
    assert json.loads((proj / "timeline.json").read_text())["title"] == "bangkok-food"


def test_group_shoots_by_gap_and_distance():
    cat = Catalog()
    bkk, bkk2, pattaya, sv = "+13.7563+100.5018/", "+13.7400+100.5600/", "+12.9236+100.8825/", "+13.6929-089.2182/"
    a = _add(cat, "/d/a.mp4", "2026-04-10T10:00:00Z", bkk)
    b = _add(cat, "/d/b.mp4", "2026-04-11T09:00:00Z", bkk2)
    c = _add(cat, "/d/c.mp4", "2026-04-11T15:00:00Z", pattaya)  # ~110 km: same shoot
    d = _add(cat, "/d/d.mp4", "2026-04-11T20:00:00Z", sv)  # other side of the world
    e = _add(cat, "/d/e.mp4", "2026-04-20T10:00:00Z", sv)  # 9-day gap
    f = _add(cat, "/old/f.mp4", None)
    groups = [[x.id for x in g] for g in group_shoots(cat.search(limit=100))]
    assert groups == [[a, b, c], [d], [e], [f]]
    assert parse_location("+13.7563+100.5018+012.000/") == (13.7563, 100.5018)

    cat.record_usage("/projects/x", [(a, 0, 3), (b, 1.5, 2), ("c_missing", 0, 1)])
    res = {s["id"]: s for s in shoots(cat, min_clips=1)}
    assert res["shoot-2026-04-10"]["unused"] == 1 and res["shoot-2026-04-10"]["clips"] == 3
    assert {x.id for x in cat.search(unused=True)} == {c, d, e, f}


def test_usage_is_replaced_per_project_and_survives_publish_flag():
    cat = Catalog()
    a, b = _add(cat, "/d/a.mp4", None), _add(cat, "/d/b.mp4", None)
    assert cat.record_usage("/p", [(a, 0, 2), (b, 0, 2)]) == 2
    cat.mark_published("/p")
    cat.record_usage("/p", [(a, 1, 2)])
    assert [(u["clip_id"], u["source_in"], u["published"]) for u in cat.usage()] == [(a, 1.0, 1)]
    assert cat.find_id("/d/b.mp4") == b and cat.find_id("c_nope") is None


def test_publish_archives_final(ws, tmp_path):
    project = tmp_path / "bangkok"
    (project / "out").mkdir(parents=True)
    (project / "out" / "final.mp4").write_bytes(b"video")
    (project / "script.md").write_text("hola")
    dest = publish(project, platform="tiktok", url="https://t/1", clips=["c_1"], today=date(2026, 11, 5))
    publish(project, platform="youtube", today=date(2026, 11, 6))
    assert dest.name == "2026-11-05-bangkok" and (dest / "final.mp4").read_bytes() == b"video"
    (meta,) = list_published()
    assert [p["platform"] for p in meta["posts"]] == ["tiktok", "youtube"] and meta["clips"] == ["c_1"]
    with pytest.raises(FileNotFoundError):
        publish(tmp_path / "empty", platform="tiktok")
    other = tmp_path / "trip2" / "bangkok"
    (other / "out").mkdir(parents=True)
    (other / "out" / "final.mp4").write_bytes(b"other")
    assert publish(other, platform="tiktok", today=date(2026, 11, 5)).name == "2026-11-05-bangkok-2"
    assert (dest / "final.mp4").read_bytes() == b"video"


@needs_ffmpeg
def test_cli_publish_records_clip_usage(ws, tmp_path):
    from vh.ingest import ingest

    clip = make_clip(tmp_path / "disk" / "a.mp4", "1080x1920")
    cat = Catalog()
    ingest([clip.parent], catalog=cat, workers=1)
    project = ws / "projects" / "2026-11-05-demo"
    assert runner.invoke(app, ["new", str(project)]).exit_code == 0
    tl = json.loads((project / "timeline.json").read_text())
    tl["video"] = [{"id": "s1", "source": str(clip), "start": 0, "duration": 2, "sourceIn": 0.5}]
    (project / "timeline.json").write_text(json.dumps(tl))
    assert runner.invoke(app, ["publish", str(project), "--platform", "tiktok"]).exit_code != 0
    assert Catalog().usage(clip_id_for(clip)) == []
    (project / "out" / "final.mp4").write_bytes(b"video")
    r = runner.invoke(app, ["publish", str(project), "--platform", "tiktok"])
    assert r.exit_code == 0, r.output
    (u,) = Catalog().usage(clip_id_for(clip))
    assert u["published"] == 1 and u["source_in"] == 0.5
    assert list_published()[0]["clips"] == [clip_id_for(clip)]
