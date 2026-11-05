from conftest import make_clip, needs_ffmpeg

from vh.catalog import Catalog, clip_id_for
from vh.ingest import ingest


@needs_ffmpeg
def test_ingest_search_annotate(tmp_path):
    root = tmp_path / "disk"
    a = make_clip(root / "DCIM" / "beach.mp4", "1080x1920")
    make_clip(root / "insta" / "VID_001.mp4", "1920x1080")
    (root / "insta" / "VID_001.lrv").write_bytes(b"proxy")
    (root / "._junk.mp4").write_bytes(b"x")
    cat = Catalog()
    r = ingest([root], catalog=cat, workers=2)
    assert r["indexed"] == 2
    assert ingest([root], catalog=cat)["skipped"] == 2

    cid = clip_id_for(a)
    c = cat.get(cid)
    assert c.orientation == "vertical" and c.duration > 2 and c.has_audio
    assert c.sheet and c.thumb

    cat.update(cid, description="Playa al atardecer con palmeras", tags="playa,sunset", rating=5)
    hits = cat.search("palmeras")
    assert [h.id for h in hits] == [cid]
    assert [h.id for h in cat.search("playa", orientation="horizontal")] == []
    assert len(cat.search(orientation="horizontal")) == 1

    ingest([root], catalog=cat, force=True)
    assert cat.get(cid).description == "Playa al atardecer con palmeras"
    assert cat.resolve(cid) == a.resolve()

    a.unlink()
    assert cat.remove_missing() == 1
