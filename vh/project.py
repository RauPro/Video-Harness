from __future__ import annotations

from pathlib import Path

from .timeline import Captions, Timeline, save_timeline

SCRIPT_TEMPLATE = """# {title}

> Notes for the editor (not spoken). Lines in [brackets] are shot/B-roll directions.
> Hook in the first 2 seconds. One idea per sentence. Short sentences cut better.

[HOOK: strongest shot first, big kinetic text]
Escribe aquí el gancho: la frase que hace que nadie haga scroll.

[CONTEXT: where we are, lower third with the location]
Contexto en una o dos frases.

[BODY: beats / list items / reveals with price stamps]
Desarrollo.

[PAYOFF + CTA]
Cierre y llamado a la acción.
"""


def new_project(path: Path, *, title: str, fmt: str, style: str) -> Path:
    path.mkdir(parents=True, exist_ok=False)
    for d in ("media", "audio", "music", "sfx", "out"):
        (path / d).mkdir()
    (path / "script.md").write_text(SCRIPT_TEMPLATE.format(title=title))
    (path / ".gitignore").write_text("media/\nout/\nsfx/\n")
    tl = Timeline(title=title, format=fmt, style=style, captions=Captions())
    save_timeline(tl, path / "timeline.json")
    return path
