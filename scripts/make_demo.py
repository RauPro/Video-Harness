"""Build a self-contained demo project from synthetic footage and an offline voice.

    uv run python scripts/make_demo.py examples/demo-bangkok && uv run vh build examples/demo-bangkok

Used by CI as the end-to-end test: footage -> voice -> captions -> timeline -> conform -> render -> QA.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from vh.project import new_project
from vh.timeline import (
    Captions,
    ComingUp,
    KineticText,
    ListHeader,
    LowerThird,
    PriceStamp,
    QuestionCard,
    Sfx,
    Transition,
    VideoClip,
    Voiceover,
    Zoom,
    load_timeline,
    save_timeline,
)
from vh.transcribe import align_to_script, narration_from_script, phrases, transcribe
from vh.tts import synthesize

SCRIPT = """# Demo: Bangkok con 500 dólares

[HOOK: kinetic text]
Vivir en Bangkok con quinientos dólares al mes.
[QUESTION CARD]
¿Es posible o es mentira?
[LOWER THIRD: Bangkok]
Hoy te enseño tres cosas que nadie te cuenta.
Uno, la renta. Un condominio con piscina cuesta trescientos dólares.
Dos, la comida. Comes increíble por dos dólares.
Tres, el transporte. El metro es rápido y barato.
Sígueme para la segunda parte.
"""

SOURCES = [
    ("testsrc2", "horizontal"),
    ("mandelbrot", "vertical"),
    ("life=s=540x960:mold=10:r=30:ratio=0.1", "vertical"),
    ("cellauto=s=1080x1920:rule=110", "vertical"),
    ("smptehdbars", "horizontal"),
    ("rgbtestsrc", "square"),
]


def footage(dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    sizes = {"horizontal": "1920x1080", "vertical": "1080x1920", "square": "1080x1080"}
    out = []
    for i, (src, orient) in enumerate(SOURCES):
        p = dest / f"clip_{i:02d}_{orient}.mp4"
        if not p.exists():
            gen = src if "=" in src else f"{src}=s={sizes[orient]}:r=30"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-t",
                    "8",
                    "-f",
                    "lavfi",
                    "-i",
                    gen,
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=f=220:d=8",
                    "-t",
                    "8",
                    "-r",
                    "30",
                    "-vf",
                    f"scale={sizes[orient].replace('x', ':')},hue=s=1.4,"
                    f"drawtext=text='CLIP {i}':fontsize=120:fontcolor=white:borderw=6:x=(w-tw)/2:y=h*0.3",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(p),
                ],
                check=True,
            )
        out.append(p)
    return out


def main(project: Path) -> None:
    if not project.exists():
        new_project(project, title="Bangkok con $500", fmt="vertical", style="raul")
    (project / "script.md").write_text(SCRIPT)
    clips = footage(project / "footage")
    voice = synthesize(narration_from_script(SCRIPT), project / "audio" / "voice", provider="espeak", language="es")
    words, _ = transcribe(voice, model="tiny", language="es")
    words = align_to_script(words, narration_from_script(SCRIPT))
    (project / "captions.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))
    ph = phrases(words)
    (project / "phrases.json").write_text(json.dumps(ph, ensure_ascii=False, indent=1))

    end = words[-1]["endMs"] / 1000 + 0.4
    tl = load_timeline(project / "timeline.json")
    tl.voiceover = Voiceover(src=voice.relative_to(project).as_posix())
    tl.captions = Captions(highlight=["bangkok", "nadie"])
    tl.duration = round(end, 2)
    # One shot per ~2.4 s, cut on phrase boundaries.
    cuts = sorted({0.0, *[round(p["start"], 2) for p in ph[1:]], round(end, 2)})
    bounds = []
    for a, b in zip(cuts, cuts[1:], strict=False):
        n = max(1, round((b - a) / 2.4))
        bounds += [(a + (b - a) * k / n, a + (b - a) * (k + 1) / n) for k in range(n)]
    tl.video = []
    for i, (a, b) in enumerate(bounds):
        src = clips[i % len(clips)]
        tl.video.append(
            VideoClip(
                id=f"s{i:02d}",
                source=str(src.relative_to(project)),
                start=round(a, 3),
                duration=round(b - a, 3),
                sourceIn=(i * 0.7) % 4,
                fit="blur" if "horizontal" in src.name else "cover",
                zoom=Zoom(start=1.0, end=1.08) if i % 2 else None,
                punchIns=[0.9] if i % 3 == 0 and b - a > 1.5 else [],
                transitionIn=Transition(type=["whip", "flash", "zoom", "glitch"][i % 4]) if i and i % 3 == 0 else None,
                grade="vivid" if i % 2 else "warm",
            )
        )
    tl.sfx = [Sfx(src="whoosh", start=c.start) for c in tl.video if c.transitionIn]
    t = {p["text"].split()[0].strip("¿,.").lower(): p for p in ph}

    def at(word: str, default: float) -> float:
        return next((p["start"] for k, p in t.items() if k.startswith(word)), default)

    tl.overlays = [
        KineticText(
            type="kineticText",
            start=0.0,
            duration=min(2.5, at("es", 2.5)),
            text="Bangkok con $500",
            highlight=["$500"],
            position="upper",
            size="xl",
            sfx="pop",
        ),
        QuestionCard(
            type="questionCard",
            start=at("es", 3),
            duration=1.6,
            kicker="PREGUNTA",
            text="¿Es posible o es mentira?",
            highlight=["mentira?"],
            sfx="click",
        ),
        LowerThird(
            type="lowerThird",
            start=at("hoy", 5),
            duration=2.4,
            kicker="Tailandia",
            title="Bangkok",
            subtitle="Raul Guillen",
            sfx="swish",
        ),
        ListHeader(type="listHeader", start=at("uno", 8), duration=2.0, number=1, title="La renta"),
        PriceStamp(
            type="priceStamp",
            start=at("uno", 8) + 2.0,
            duration=1.8,
            amount="$300",
            label="Condominio",
            sublabel="al mes",
            sfx="cash",
        ),
        ListHeader(type="listHeader", start=at("dos", 12), duration=2.0, number=2, title="La comida"),
        ListHeader(type="listHeader", start=at("tres", 16), duration=2.0, number=3, title="El transporte"),
        ComingUp(type="comingUp", start=max(0.0, end - 2.2), duration=2.0, text="PARTE 2..."),
    ]
    tl.overlays = [o for o in tl.overlays if o.start + o.duration <= end]
    save_timeline(tl, project / "timeline.json")
    print(f"demo project ready: {project} ({end:.1f}s, {len(tl.video)} shots)")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "examples/demo-bangkok"))
