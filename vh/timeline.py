"""Timeline model: the single contract between the agent (author) and the renderer.

All times are in seconds on the output timeline unless the field name says otherwise.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Format = Literal["vertical", "horizontal", "square"]
FORMAT_SIZES: dict[str, tuple[int, int]] = {
    "vertical": (1080, 1920),
    "horizontal": (1920, 1080),
    "square": (1080, 1080),
}
Position = Literal["top", "upper", "center", "lower", "bottom"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Transition(Model):
    type: Literal["cut", "whip", "flash", "zoom", "fade", "glitch", "slide"] = "cut"
    duration: float = Field(0.25, gt=0, le=2)
    direction: Literal["left", "right", "up", "down"] = "left"
    color: str = "#ffffff"


class Zoom(Model):
    start: float = Field(1.0, ge=0.5, le=3, description="Scale at clip start (Ken Burns).")
    end: float = Field(1.0, ge=0.5, le=3, description="Scale at clip end.")
    focusX: float = Field(0.5, ge=0, le=1)
    focusY: float = Field(0.5, ge=0, le=1)


class Reframe(Model):
    """Reframe a 360 equirectangular source into a flat view (Insta360 exports)."""

    yaw: float = Field(0, ge=-180, le=180)
    pitch: float = Field(0, ge=-90, le=90)
    roll: float = Field(0, ge=-180, le=180)
    fov: float = Field(100, ge=30, le=170)


class VideoClip(Model):
    id: str
    source: str = Field(description="Catalog clip id (e.g. 'c_1a2b3c4d') or a file path.")
    kind: Literal["video", "image"] = "video"
    start: float = Field(ge=0, description="Start on the output timeline.")
    duration: float = Field(gt=0)
    sourceIn: float = Field(0, ge=0, description="Offset into the source where this shot begins.")
    speed: float = Field(1.0, gt=0.1, le=8)
    volume: float = Field(0.0, ge=0, le=2, description="Natural sound level (0 = muted).")
    fit: Literal["cover", "contain", "blur"] = "cover"
    zoom: Zoom | None = None
    punchIns: list[float] = Field(default_factory=list, description="Seconds from clip start; scale jumps.")
    punchScale: float = Field(1.15, ge=1, le=2)
    transitionIn: Transition | None = None
    reframe: Reframe | None = None
    grade: Literal["none", "warm", "cool", "vivid", "bw", "film"] = "none"
    note: str = ""
    src: str | None = Field(None, description="Set by `vh conform`: conformed file relative to project.")
    srcIn: float | None = Field(None, description="Set by `vh conform`: offset inside the conformed file.")

    @property
    def end(self) -> float:
        return self.start + self.duration


class _Overlay(Model):
    start: float = Field(ge=0)
    duration: float = Field(gt=0)
    sfx: str | None = Field(None, description="Optional sound effect played at overlay start.")

    @property
    def end(self) -> float:
        return self.start + self.duration


class KineticText(_Overlay):
    type: Literal["kineticText"]
    text: str
    highlight: list[str] = Field(default_factory=list)
    position: Position = "center"
    size: Literal["m", "l", "xl"] = "l"
    animation: Literal["pop", "slide", "typewriter", "stack"] = "pop"
    color: str | None = None
    highlightColor: str | None = None


class PriceStamp(_Overlay):
    type: Literal["priceStamp"]
    amount: str
    label: str | None = None
    sublabel: str | None = None
    variant: Literal["badge", "bubble", "slime"] = "badge"
    position: Position = "center"
    color: str | None = None


class LowerThird(_Overlay):
    type: Literal["lowerThird"]
    title: str
    kicker: str | None = None
    subtitle: str | None = None
    variant: Literal["stack", "tag"] = "stack"
    position: Position = "lower"


class ListHeader(_Overlay):
    type: Literal["listHeader"]
    number: int | str
    title: str
    subtitle: str | None = None
    position: Position = "top"


class ComingUp(_Overlay):
    type: Literal["comingUp"]
    text: str = "COMING UP..."


class QuestionCard(_Overlay):
    type: Literal["questionCard"]
    text: str
    kicker: str = "QUESTION"
    highlight: list[str] = Field(default_factory=list)


class Flash(_Overlay):
    type: Literal["flash"]
    color: str = "#ffffff"
    opacity: float = Field(0.9, ge=0, le=1)


class ArrowCallout(_Overlay):
    type: Literal["arrowCallout"]
    text: str = ""
    x: float = Field(0.5, ge=0, le=1, description="Arrow tip, fraction of width.")
    y: float = Field(0.5, ge=0, le=1, description="Arrow tip, fraction of height.")
    angle: float = Field(-135, description="Degrees; direction the arrow comes from.")
    color: str = "#ff2a2a"


class InfoRow(Model):
    left: str
    right: str = ""


class InfoCard(_Overlay):
    type: Literal["infoCard"]
    title: str | None = None
    rows: list[InfoRow]
    accent: str | None = None
    position: Position = "upper"


class ImageInsert(_Overlay):
    type: Literal["imageInsert"]
    src: str = Field(description="Image/video path relative to the project, absolute path, or catalog id.")
    media: str | None = Field(None, description="Set by `vh conform`: file to render, relative to project.")
    mediaSrc: str | None = Field(None, description="Set by `vh conform`: the `src` that `media` was made from.")
    frame: Literal["phone", "polaroid", "none"] = "phone"
    background: Literal["paper-red", "paper-blue", "blur", "none"] = "none"
    x: float = Field(0.5, ge=0, le=1)
    y: float = Field(0.5, ge=0, le=1)
    scale: float = Field(0.6, gt=0, le=1.5)
    rotate: float = 0


class Emoji(_Overlay):
    type: Literal["emoji"]
    emoji: str
    x: float = Field(0.5, ge=0, le=1)
    y: float = Field(0.3, ge=0, le=1)
    size: float = Field(180, gt=10, le=800)


class ProgressBar(_Overlay):
    type: Literal["progressBar"]
    color: str | None = None


Overlay = Annotated[
    KineticText
    | PriceStamp
    | LowerThird
    | ListHeader
    | ComingUp
    | QuestionCard
    | Flash
    | ArrowCallout
    | InfoCard
    | ImageInsert
    | Emoji
    | ProgressBar,
    Field(discriminator="type"),
]


class Sfx(Model):
    src: str = Field(description="Library name (e.g. 'whoosh') or a path relative to the project.")
    start: float = Field(ge=0)
    volume: float = Field(0.6, ge=0, le=2)


class Voiceover(Model):
    src: str
    start: float = 0
    volume: float = 1.0


class Music(Model):
    src: str
    start: float = 0
    sourceIn: float = 0
    volume: float = Field(0.22, ge=0, le=1)
    duckTo: float = Field(0.07, ge=0, le=1, description="Music level while someone is speaking.")
    fadeIn: float = 0.5
    fadeOut: float = 1.5


class Captions(Model):
    src: str = "captions.json"
    preset: Literal["bold-pop", "karaoke", "subtle", "none"] | None = None
    position: Position | None = None
    maxWords: int | None = Field(None, ge=1, le=8)
    uppercase: bool | None = None
    highlight: list[str] = Field(default_factory=list, description="Words always drawn in highlight color.")
    hideDuring: list[tuple[float, float]] = Field(
        default_factory=list, description="[start, end] ranges where captions are hidden (e.g. full cards)."
    )


class Timeline(Model):
    version: Literal[1] = 1
    title: str = ""
    format: Format = "vertical"
    fps: int = Field(30, ge=12, le=60)
    style: str = "raul"
    duration: float | None = Field(None, gt=0, description="Defaults to the end of the last element.")
    voiceover: Voiceover | None = None
    music: Music | None = None
    captions: Captions | None = None
    video: list[VideoClip] = Field(default_factory=list)
    overlays: list[Overlay] = Field(default_factory=list)
    sfx: list[Sfx] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _unique_ids(self) -> Timeline:
        ids = [c.id for c in self.video]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"duplicate video clip ids: {sorted(dupes)}")
        return self

    @property
    def size(self) -> tuple[int, int]:
        return FORMAT_SIZES[self.format]

    def computed_duration(self) -> float:
        if self.duration:
            return self.duration
        ends = [c.end for c in self.video] + [o.end for o in self.overlays]
        return max(ends, default=1.0)


def load_timeline(path: Path) -> Timeline:
    return Timeline.model_validate_json(Path(path).read_text())


def save_timeline(tl: Timeline, path: Path) -> None:
    Path(path).write_text(tl.model_dump_json(indent=2, exclude_none=True) + "\n")


def lint_errors(tl: Timeline) -> list[str]:
    """Problems that make the render wrong (black gaps, overlapping shots); `vh build` refuses to run with these."""
    errors: list[str] = []
    frame = 1.0 / tl.fps
    total = tl.computed_duration()
    clips = sorted(tl.video, key=lambda c: c.start)
    if not clips:
        errors.append("timeline has no video clips")
    cursor = 0.0
    for c in clips:
        if c.start - cursor > frame:
            errors.append(f"gap (black frames) {cursor:.2f}s-{c.start:.2f}s before clip {c.id}")
        if cursor - c.start > frame:
            errors.append(f"clip {c.id} overlaps previous clip by {cursor - c.start:.2f}s")
        cursor = max(cursor, c.end)
    if clips and total - cursor > frame:
        errors.append(f"no video from {cursor:.2f}s to end {total:.2f}s")
    return errors


def lint_timeline(tl: Timeline, voice_duration: float | None = None) -> list[str]:
    """Return human-readable problems the schema can't express: `lint_errors` first, then advisory warnings."""
    warnings: list[str] = lint_errors(tl)
    frame = 1.0 / tl.fps
    total = tl.computed_duration()
    clips = sorted(tl.video, key=lambda c: c.start)
    for o in tl.overlays:
        if o.end > total + frame:
            warnings.append(f"overlay {o.type}@{o.start:.2f}s ends after the video ({total:.2f}s)")
    for c in clips:
        if c.duration > 12:
            warnings.append(f"clip {c.id} is {c.duration:.1f}s long; consider cutting or punching in")
        for p in c.punchIns:
            if not 0 <= p < c.duration:
                warnings.append(f"clip {c.id} punchIn {p}s is outside the clip")
    if voice_duration is not None and abs(voice_duration - total) > 1.0:
        warnings.append(f"voiceover is {voice_duration:.2f}s but timeline is {total:.2f}s")
    return warnings


def export_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(Timeline.model_json_schema(), indent=2) + "\n")
