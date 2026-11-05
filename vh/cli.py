from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from . import paths
from .catalog import Catalog

app = typer.Typer(help="Video-Harness: footage -> script -> voice -> timeline -> render -> QA.", no_args_is_help=True)
console = Console()

ProjectArg = Annotated[Path, typer.Argument(help="Project directory (contains timeline.json).")]


def _tl(project: Path):
    from .timeline import load_timeline

    return load_timeline(project / "timeline.json")


def _fail(msg: str) -> None:
    console.print(f"[red]error:[/red] {msg}")
    raise typer.Exit(1)


# ---------------------------------------------------------------- setup
@app.command()
def doctor() -> None:
    """Check external tools, renderer deps and API keys."""
    import os

    rows = [
        ("ffmpeg", bool(shutil.which("ffmpeg"))),
        ("ffprobe", bool(shutil.which("ffprobe"))),
        ("node/npx", bool(shutil.which("npx"))),
        ("renderer deps", (paths.RENDERER_DIR / "node_modules" / "remotion").exists()),
        ("sfx library", (paths.SFX_DIR / "whoosh.wav").exists()),
        ("yt-dlp (optional)", bool(shutil.which("yt-dlp"))),
        ("espeak-ng (optional)", bool(shutil.which("espeak-ng") or shutil.which("espeak"))),
        ("ELEVENLABS_API_KEY (optional)", bool(os.environ.get("ELEVENLABS_API_KEY"))),
        ("OPENAI_API_KEY (optional)", bool(os.environ.get("OPENAI_API_KEY"))),
    ]
    t = Table("check", "ok")
    for name, ok in rows:
        t.add_row(name, "[green]yes[/green]" if ok else "[yellow]no[/yellow]")
    console.print(t)
    console.print(f"catalog: {paths.catalog_path()}  cache: {paths.cache_dir()}")


@app.command()
def setup() -> None:
    """Install renderer node deps and generate the SFX library."""
    from .sfx import generate

    generate(paths.SFX_DIR)
    npm = shutil.which("npm")
    if not npm:
        _fail("npm not found; install Node.js 20+")
    subprocess.run(
        [npm, "ci" if (paths.RENDERER_DIR / "package-lock.json").exists() else "install"],
        cwd=paths.RENDERER_DIR,
        check=True,
    )
    console.print("[green]ready[/green]")


@app.command()
def schema() -> None:
    """Regenerate schemas/timeline.schema.json from the timeline model."""
    from .timeline import export_schema

    export_schema(paths.SCHEMA_PATH)
    console.print(f"wrote {paths.SCHEMA_PATH}")


# ---------------------------------------------------------------- footage library
@app.command()
def ingest(
    roots: Annotated[list[Path], typer.Argument(help="Folders or files to index (e.g. /Volumes/Insta360).")],
    transcribe: Annotated[bool, typer.Option(help="Transcribe clips with speech (slower).")] = False,
    scenes: Annotated[bool, typer.Option(help="Detect scene changes.")] = True,
    workers: int = 4,
    model: str = "small",
    force: bool = False,
) -> None:
    """Index footage in place (incremental: unchanged files are skipped)."""
    from .ingest import ingest as run

    cat = Catalog()
    with console.status("indexing...") as status:
        counts = run(
            roots,
            catalog=cat,
            workers=workers,
            scenes=scenes,
            force=force,
            on_progress=lambda msg, p: status.update(f"{msg}: {p.name}"),
        )
    console.print(counts)
    if transcribe:
        _transcribe_catalog(cat, model=model)


def _transcribe_catalog(cat: Catalog, model: str, ids: list[str] | None = None) -> None:
    from .transcribe import plain_text, transcribe

    rows = [cat.get(i) for i in ids] if ids else cat.search(limit=10**9)
    todo = [c for c in rows if c and c.kind == "video" and c.has_audio and (c.duration or 0) > 2 and not c.transcript]
    for i, c in enumerate(todo, 1):
        console.print(f"[{i}/{len(todo)}] transcribing {Path(c.path).name}")
        try:
            words, lang = transcribe(Path(c.path), model=model)
        except Exception as e:  # noqa: BLE001
            console.print(f"  [yellow]skip[/yellow]: {e}")
            continue
        cat.update(c.id, transcript=plain_text(words), words=json.dumps(words), language=lang)


@app.command("transcribe-clips")
def transcribe_clips(ids: Annotated[list[str] | None, typer.Argument()] = None, model: str = "small") -> None:
    """Transcribe catalog clips (all untranscribed ones, or the given ids)."""
    _transcribe_catalog(Catalog(), model=model, ids=ids)


@app.command()
def search(
    query: Annotated[str | None, typer.Argument(help="Words matched against transcript/description/tags/path.")] = None,
    orientation: Annotated[str | None, typer.Option(help="vertical|horizontal|square|equirect")] = None,
    min_duration: float | None = None,
    max_duration: float | None = None,
    speech: Annotated[bool | None, typer.Option(help="Only clips with (or without) speech.")] = None,
    undescribed: bool = False,
    after: Annotated[str | None, typer.Option(help="ISO date, e.g. 2026-04-01")] = None,
    before: str | None = None,
    path: Annotated[str | None, typer.Option(help="Substring of the file path (folder/trip name).")] = None,
    limit: int = 30,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Find clips in the catalog."""
    res = Catalog().search(
        query,
        orientation=orientation,
        min_duration=min_duration,
        max_duration=max_duration,
        has_speech=speech,
        undescribed=undescribed,
        after=after,
        before=before,
        path_like=path,
        limit=limit,
    )
    if as_json:
        keys = ("id", "path", "duration", "orientation", "created_at", "description", "tags", "sheet", "transcript")
        print(json.dumps([{k: c.row[k] for k in keys} for c in res], ensure_ascii=False, indent=1))
        return
    t = Table("id", "dur", "orient", "date", "file", "description / transcript")
    for c in res:
        desc = c.description or (c.transcript or "")[:80]
        t.add_row(
            c.id, f"{c.duration or 0:.1f}", c.orientation or "", (c.created_at or "")[:10], Path(c.path).name, desc
        )
    console.print(t)


@app.command()
def show(clip_id: str) -> None:
    """Show everything known about a clip (incl. contact sheet path to look at)."""
    c = Catalog().get(clip_id)
    if not c:
        _fail(f"{clip_id} not found")
    print(json.dumps(c.to_dict(), ensure_ascii=False, indent=2))


@app.command()
def describe(
    clip_id: str,
    text: Annotated[str | None, typer.Option(help="What happens in the clip (visual description).")] = None,
    tags: Annotated[str | None, typer.Option(help="Comma-separated tags, e.g. 'bangkok,street-food,night'.")] = None,
    rating: Annotated[int | None, typer.Option(min=0, max=5)] = None,
) -> None:
    """Annotate a clip after looking at its contact sheet; makes it searchable."""
    fields = {k: v for k, v in {"description": text, "tags": tags, "rating": rating}.items() if v is not None}
    Catalog().update(clip_id, **fields)
    console.print(f"updated {clip_id}")


@app.command()
def stats() -> None:
    """Catalog totals."""
    s = Catalog().stats()
    console.print(s)


@app.command()
def prune() -> None:
    """Remove catalog entries whose files no longer exist (e.g. disk unplugged? don't run then)."""
    console.print(f"removed {Catalog().remove_missing()}")


# ---------------------------------------------------------------- project
@app.command()
def new(
    project: ProjectArg,
    title: str = "",
    format: Annotated[str, typer.Option(help="vertical|horizontal|square")] = "vertical",
    style: str = "raul",
) -> None:
    """Create a project skeleton (script.md, timeline.json, media/, audio/, ...)."""
    from .project import new_project
    from .styles import load_theme

    load_theme(style)
    new_project(project, title=title or project.name, fmt=format, style=style)
    console.print(f"created {project}; write script.md next")


@app.command()
def styles() -> None:
    """List editing styles."""
    from .styles import list_styles, load_theme

    for s in list_styles():
        th = load_theme(s)
        console.print(f"[bold]{s}[/bold]: {th.get('description', '')}")


@app.command()
def voiceover(
    project: ProjectArg,
    provider: Annotated[str, typer.Option(help="elevenlabs|openai|espeak")] = "elevenlabs",
    voice: str | None = None,
    model: str | None = None,
    language: str = "es",
    instructions: Annotated[str | None, typer.Option(help="OpenAI only: delivery/tone directions.")] = None,
) -> None:
    """Generate voice from script.md narration into audio/voice.*, and set it in timeline.json."""
    from .timeline import Voiceover, save_timeline
    from .transcribe import narration_from_script
    from .tts import synthesize

    text = narration_from_script((project / "script.md").read_text())
    if not text:
        _fail("script.md has no narration")
    out = synthesize(
        text,
        project / "audio" / "voice",
        provider=provider,
        voice=voice,
        model=model,
        language=language,
        instructions=instructions,
    )
    tl = _tl(project)
    tl.voiceover = Voiceover(src=out.relative_to(project).as_posix())
    save_timeline(tl, project / "timeline.json")
    console.print(f"wrote {out}; next: vh captions {project}")


@app.command()
def captions(
    project: ProjectArg,
    audio: Annotated[Path | None, typer.Option(help="Audio to caption (default: timeline voiceover).")] = None,
    script: Annotated[bool, typer.Option(help="Align words to script.md spelling.")] = True,
    model: str = "small",
    language: str | None = "es",
) -> None:
    """Word-level captions (captions.json) + phrases.json for cutting on phrase boundaries."""
    from .timeline import Captions, save_timeline
    from .transcribe import align_to_script, narration_from_script, phrases, transcribe

    tl = _tl(project)
    src = audio or (project / tl.voiceover.src if tl.voiceover else None)
    if not src:
        _fail("no audio: run `vh voiceover` or pass --audio (e.g. your own recorded voice)")
    words, lang = transcribe(Path(src), model=model, language=language)
    if script and (project / "script.md").exists():
        narration = narration_from_script((project / "script.md").read_text())
        if narration:
            words = align_to_script(words, narration)
    (project / "captions.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))
    (project / "phrases.json").write_text(json.dumps(phrases(words), ensure_ascii=False, indent=1))
    if tl.captions is None:
        tl.captions = Captions()
        save_timeline(tl, project / "timeline.json")
    console.print(f"{len(words)} words ({lang}); wrote captions.json and phrases.json")


@app.command()
def segments(project: ProjectArg) -> None:
    """Print phrases with timings and the shot budget the style's pacing implies."""
    from .styles import load_theme

    tl = _tl(project)
    pacing = load_theme(tl.style)["pacing"]
    ph = json.loads((project / "phrases.json").read_text())
    t = Table("#", "start", "end", "shots", "text")
    for i, p in enumerate(ph):
        n = max(1, round((p["end"] - p["start"]) / pacing["avgShotSeconds"]))
        t.add_row(str(i), f"{p['start']:.2f}", f"{p['end']:.2f}", str(n), p["text"])
    console.print(t)
    console.print(f"style {tl.style}: avg shot {pacing['avgShotSeconds']}s, max {pacing['maxShotSeconds']}s")


@app.command()
def validate(project: ProjectArg) -> None:
    """Validate timeline.json against the schema and lint it."""
    from pydantic import ValidationError

    from .render import voice_duration
    from .styles import load_theme
    from .timeline import lint_timeline

    try:
        tl = _tl(project)
        load_theme(tl.style)
    except (ValidationError, KeyError) as e:
        _fail(str(e))
    warnings = lint_timeline(tl, voice_duration(tl, project))
    for w in warnings:
        console.print(f"[yellow]warning[/yellow]: {w}")
    console.print(
        f"[green]valid[/green] ({len(tl.video)} clips, {len(tl.overlays)} overlays, {tl.computed_duration():.2f}s)"
    )


@app.command()
def conform(project: ProjectArg, workers: int = 3, force: bool = False) -> None:
    """Cut, reframe and normalize every shot into project/media/."""
    from .conform import conform as run
    from .timeline import save_timeline

    tl = _tl(project)
    with console.status("conforming..."):
        run(tl, project, Catalog(), workers=workers, force=force)
    save_timeline(tl, project / "timeline.json")
    console.print(f"conformed {len(tl.video)} clips")


@app.command()
def render(
    project: ProjectArg,
    preview: Annotated[bool, typer.Option(help="Half resolution, fast.")] = False,
    out: Path | None = None,
    master: Annotated[bool, typer.Option(help="Loudness-normalize audio to -14 LUFS.")] = True,
    concurrency: int | None = None,
) -> None:
    """Render with Remotion to out/final.mp4 (or out/preview.mp4)."""
    from .render import render as run

    tl = _tl(project)
    dest = out or project / "out" / ("preview.mp4" if preview else "final.mp4")
    run(tl, project, dest, preview=preview, master=master, concurrency=concurrency)
    console.print(f"[green]rendered[/green] {dest}")


@app.command()
def still(project: ProjectArg, at: Annotated[float, typer.Option(help="Seconds")] = 0.0) -> None:
    """Render one frame (fast visual check of an overlay/caption)."""
    from .render import still as run

    out = run(_tl(project), project, at, project / "out" / "stills" / f"{at:07.2f}.png")
    console.print(str(out))


@app.command()
def qa(project: ProjectArg, video: Path | None = None) -> None:
    """Check the render: duration, loudness, black frames, safe zones; writes out/qa.json + frames."""
    from .qa import run_qa
    from .render import voice_duration

    tl = _tl(project)
    v = video or next((p for p in [project / "out" / "final.mp4", project / "out" / "preview.mp4"] if p.exists()), None)
    if not v:
        _fail("no render found; run `vh render` first")
    report = run_qa(tl, v, project, voice_duration(tl, project))
    for i in report["issues"]:
        console.print(f"[red]issue[/red]: {i}")
    for w in report["warnings"]:
        console.print(f"[yellow]warning[/yellow]: {w}")
    console.print(f"loudness: {report['loudness']}\nsheet: {report['sheet']}")
    if not report["ok"]:
        raise typer.Exit(2)


@app.command()
def build(project: ProjectArg, preview: bool = False) -> None:
    """validate -> conform -> render -> qa."""
    validate(project)
    conform(project)
    render(project, preview=preview, out=None, master=True, concurrency=None)
    qa(project, None)


# ---------------------------------------------------------------- styles / references
@app.command("analyze-ref")
def analyze_ref(
    source: Annotated[str, typer.Argument(help="Local video file or URL (YouTube/TikTok via yt-dlp).")],
    name: Annotated[str, typer.Option(help="Folder name under references/.")] = "",
    section: Annotated[str | None, typer.Option(help="Only download a section, e.g. 0-240")] = None,
    transcribe: bool = False,
) -> None:
    """Measure a reference video's pacing (cuts/min, shot lengths, loudness) + contact sheets."""
    from .style_analyze import analyze, fetch

    slug = name or Path(source).stem or "ref"
    out = paths.REPO_ROOT / "references" / slug
    video = fetch(source, out, section) if source.startswith("http") else Path(source)
    res = analyze(video, out, transcribe=transcribe)
    print(json.dumps({k: v for k, v in res.items() if k != "sheets"}, indent=2, ensure_ascii=False))
    console.print(f"contact sheets: {res['sheets']}")


@app.command("sfx")
def sfx_cmd(regenerate: bool = False) -> None:
    """List (and generate) the built-in sound-effect library."""
    from .sfx import LIBRARY, generate

    generate(paths.SFX_DIR, force=regenerate)
    console.print(", ".join(LIBRARY))


if __name__ == "__main__":
    app()
