import json

import pytest
from pydantic import ValidationError

from vh.paths import SCHEMA_PATH
from vh.timeline import Timeline, VideoClip, lint_timeline, load_timeline, save_timeline


def clip(i, start, dur, **kw):
    return VideoClip(id=f"s{i}", source="a.mp4", start=start, duration=dur, **kw)


def test_roundtrip(tmp_path):
    tl = Timeline(
        title="t",
        video=[clip(0, 0, 2)],
        overlays=[
            {"type": "priceStamp", "start": 0.5, "duration": 1, "amount": "$10"},
            {"type": "lowerThird", "start": 0, "duration": 1, "title": "Bangkok"},
        ],
    )
    p = tmp_path / "timeline.json"
    save_timeline(tl, p)
    back = load_timeline(p)
    assert back == tl
    assert back.overlays[0].type == "priceStamp"
    assert back.size == (1080, 1920)


def test_formats():
    assert Timeline(format="horizontal").size == (1920, 1080)
    assert Timeline(format="square").size == (1080, 1080)


def test_rejects_unknown_overlay_and_fields():
    with pytest.raises(ValidationError):
        Timeline(overlays=[{"type": "nope", "start": 0, "duration": 1}])
    with pytest.raises(ValidationError):
        Timeline.model_validate({"video": [{"id": "a", "source": "x", "start": 0, "duration": 1, "bogus": 1}]})


def test_duplicate_clip_ids():
    with pytest.raises(ValidationError):
        Timeline(video=[clip(0, 0, 1), clip(0, 1, 1)])


def test_lint_gaps_overlaps_and_voice():
    tl = Timeline(video=[clip(0, 0, 2), clip(1, 2.5, 2), clip(2, 4, 1)])
    w = "\n".join(lint_timeline(tl, voice_duration=9))
    assert "gap" in w and "overlaps" in w and "voiceover" in w
    assert lint_timeline(Timeline(video=[clip(0, 0, 2), clip(1, 2, 2)]), voice_duration=4) == []


def test_lint_punch_and_overlay_bounds():
    tl = Timeline(
        duration=2, video=[clip(0, 0, 2, punchIns=[3])], overlays=[{"type": "flash", "start": 1.5, "duration": 2}]
    )
    w = "\n".join(lint_timeline(tl))
    assert "punchIn" in w and "ends after" in w


def test_committed_schema_is_current():
    assert json.loads(SCHEMA_PATH.read_text()) == Timeline.model_json_schema(), "run `vh schema`"
