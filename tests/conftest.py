import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setenv("VH_DATA", str(tmp_path / "vhdata"))
    monkeypatch.setenv("VH_CATALOG", str(tmp_path / "vhdata" / "catalog.db"))
    monkeypatch.setenv("VH_CACHE", str(tmp_path / "vhdata" / "cache"))


needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def make_clip(path: Path, size: str = "1280x720", seconds: float = 3, color: str = "testsrc2") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-t",
            str(seconds),
            "-f",
            "lavfi",
            "-i",
            f"{color}=s={size}:r=30",
            "-t",
            str(seconds),
            "-f",
            "lavfi",
            "-i",
            "sine=f=440",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
    )
    return path
