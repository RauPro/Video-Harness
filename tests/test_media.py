import wave

from conftest import make_clip, needs_ffmpeg

from vh.catalog import Catalog
from vh.conform import build_filter, conform
from vh.ffmpeg import probe
from vh.sfx import LIBRARY
from vh.sfx import generate as generate_sfx
from vh.timeline import Reframe, Timeline, VideoClip


def test_filters():
    c = VideoClip(id="a", source="x", start=0, duration=1, fit="blur")
    assert "boxblur" in build_filter(c, 1080, 1920, 30, 1920, 1080)
    r = VideoClip(id="b", source="x", start=0, duration=1, reframe=Reframe(yaw=90, pitch=-10, fov=100))
    f = build_filter(r, 1080, 1920, 30, 5760, 2880)
    assert "v360=input=e:output=flat:yaw=90" in f and "w=1080:h=1920" in f


def test_sfx_library(tmp_path):
    paths = generate_sfx(tmp_path)
    assert len(paths) == len(LIBRARY)
    with wave.open(str(paths[0])) as wf:
        assert wf.getnframes() > 0


@needs_ffmpeg
def test_conform_cuts_and_crops(tmp_path):
    project = tmp_path / "proj"
    src = make_clip(tmp_path / "wide.mp4", "1920x1080", seconds=4)
    tl = Timeline(
        fps=30,
        video=[
            VideoClip(id="a", source=str(src), start=0, duration=1.5, sourceIn=1, fit="cover"),
            VideoClip(id="b", source=str(src), start=1.5, duration=1, fit="blur", speed=2),
        ],
    )
    out = conform(tl, project, Catalog(), workers=2)
    for c in out.video:
        info = probe(project / "public" / c.src) if (project / "public" / c.src).exists() else probe(project / c.src)
        assert info.display_size == (1080, 1920)
        assert info.duration >= c.duration
