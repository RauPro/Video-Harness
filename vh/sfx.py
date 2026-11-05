"""Procedurally generated, royalty-free sound effects (no licensing questions)."""

from __future__ import annotations

import wave
from collections.abc import Callable
from pathlib import Path

import numpy as np

SR = 48000
_rng = np.random.default_rng(7)


def _t(sec: float) -> np.ndarray:
    return np.arange(int(SR * sec)) / SR


def _env(n: int, attack: float, release_pow: float = 2.0) -> np.ndarray:
    a = max(1, int(n * attack))
    return np.concatenate([np.linspace(0, 1, a), np.linspace(1, 0, n - a) ** release_pow])


def _bandpass(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    f = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    f[(freqs < lo) | (freqs > hi)] = 0
    return np.fft.irfft(f, len(x))


def _sweep_noise(sec: float, f0: float, f1: float, bands: int = 24) -> np.ndarray:
    n = int(SR * sec)
    noise = _rng.standard_normal(n)
    out = np.zeros(n)
    edges = np.linspace(0, n, bands + 1).astype(int)
    for i in range(bands):
        fc = f0 * (f1 / f0) ** (i / (bands - 1))
        seg = _bandpass(noise, fc * 0.6, fc * 1.6)
        w = np.zeros(n)
        lo, hi = max(0, edges[i] - n // bands), min(n, edges[i + 1] + n // bands)
        w[lo:hi] = np.hanning(hi - lo)
        out += seg * w
    return out


def whoosh() -> np.ndarray:
    x = _sweep_noise(0.45, 300, 4500)
    return x * _env(len(x), 0.6, 1.5)


def swish() -> np.ndarray:
    x = _sweep_noise(0.22, 1200, 7000, bands=12)
    return x * _env(len(x), 0.35, 1.5)


def pop() -> np.ndarray:
    t = _t(0.12)
    f = 900 * np.exp(-t * 30) + 200
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.02, 3)


def click() -> np.ndarray:
    x = _bandpass(_rng.standard_normal(int(SR * 0.03)), 2000, 9000)
    return x * _env(len(x), 0.05, 4)


def ding() -> np.ndarray:
    t = _t(0.9)
    x = np.sin(2 * np.pi * 1318.5 * t) + 0.6 * np.sin(2 * np.pi * 1760 * t) + 0.2 * np.sin(2 * np.pi * 2637 * t)
    return x * np.exp(-t * 5)


def cash() -> np.ndarray:
    t = _t(0.9)
    bell = (np.sin(2 * np.pi * 2093 * t) + 0.7 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 6)
    rattle = _bandpass(_rng.standard_normal(len(t)), 3000, 10000) * np.exp(-t * 18) * 0.6
    return np.concatenate([np.zeros(int(SR * 0.04)), bell])[: len(t)] + rattle


def riser() -> np.ndarray:
    t = _t(1.4)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * (t / t[-1]) ** 2) / SR) * 0.5
    noise = _sweep_noise(1.4, 400, 8000) * 0.8
    return (tone + noise) * np.linspace(0, 1, len(t)) ** 2


def boom() -> np.ndarray:
    t = _t(0.9)
    f = 40 + 90 * np.exp(-t * 12)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    return np.tanh(2.5 * x)


def glitch() -> np.ndarray:
    parts = []
    for _ in range(9):
        d = _rng.uniform(0.015, 0.045)
        t = _t(d)
        sq = np.sign(np.sin(2 * np.pi * _rng.uniform(80, 1400) * t)) * _rng.uniform(0.3, 1)
        parts += [sq, np.zeros(int(SR * _rng.uniform(0, 0.02)))]
    return np.concatenate(parts)


def typing() -> np.ndarray:
    out = np.zeros(int(SR * 0.7))
    for start in np.cumsum(_rng.uniform(0.05, 0.11, 9)):
        c = click() * _rng.uniform(0.5, 1)
        i = int(start * SR)
        n = min(len(c), len(out) - i)
        if n <= 0:
            break
        out[i : i + n] += c[:n]
    return out


def shutter() -> np.ndarray:
    a, b = click(), click()
    return np.concatenate([a, np.zeros(int(SR * 0.07)), b * 0.8])


def record_scratch() -> np.ndarray:
    t = _t(0.5)
    f = 1800 * (1 - t / t[-1]) ** 2 + 120
    tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3
    return (tone + _bandpass(_rng.standard_normal(len(t)), 500, 6000) * 0.5) * _env(len(t), 0.05, 1.2)


LIBRARY: dict[str, Callable[[], np.ndarray]] = {
    "whoosh": whoosh,
    "swish": swish,
    "pop": pop,
    "click": click,
    "ding": ding,
    "cash": cash,
    "riser": riser,
    "boom": boom,
    "glitch": glitch,
    "typing": typing,
    "shutter": shutter,
    "scratch": record_scratch,
}


def write_wav(path: Path, x: np.ndarray, peak_db: float = -3.0) -> None:
    x = x / (np.max(np.abs(x)) or 1) * 10 ** (peak_db / 20)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    stereo = np.column_stack([pcm, pcm]).ravel()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


def generate(out_dir: Path, force: bool = False) -> list[Path]:
    paths = []
    for name, fn in LIBRARY.items():
        p = out_dir / f"{name}.wav"
        if force or not p.exists():
            write_wav(p, fn())
        paths.append(p)
    return paths
