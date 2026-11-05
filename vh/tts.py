"""Voiceover providers. All return a path to an audio file; timing comes from `vh captions`."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import httpx

PROVIDERS = ("elevenlabs", "openai", "espeak")


class TTSError(RuntimeError):
    pass


def synthesize(
    text: str,
    out: Path,
    *,
    provider: str,
    voice: str | None = None,
    model: str | None = None,
    language: str = "es",
    instructions: str | None = None,
) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if provider == "elevenlabs":
        return _elevenlabs(text, out.with_suffix(".mp3"), voice=voice, model=model)
    if provider == "openai":
        return _openai(text, out.with_suffix(".mp3"), voice=voice, model=model, instructions=instructions)
    if provider == "espeak":
        return _espeak(text, out.with_suffix(".wav"), voice=voice or language)
    raise TTSError(f"unknown provider {provider!r}; choose one of {PROVIDERS}")


def _key(name: str) -> str:
    key = os.environ.get(name)
    if not key:
        raise TTSError(f"{name} is not set")
    return key


def _elevenlabs(text: str, out: Path, *, voice: str | None, model: str | None) -> Path:
    voice_id = voice or os.environ.get("ELEVENLABS_VOICE_ID")
    if not voice_id:
        raise TTSError("pass --voice <voice_id> or set ELEVENLABS_VOICE_ID (your cloned voice works best)")
    r = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": _key("ELEVENLABS_API_KEY")},
        json={
            "text": text,
            "model_id": model or "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True},
        },
        timeout=300,
    )
    if r.status_code != 200:
        raise TTSError(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    out.write_bytes(r.content)
    return out


def _openai(text: str, out: Path, *, voice: str | None, model: str | None, instructions: str | None) -> Path:
    body = {"model": model or "gpt-4o-mini-tts", "voice": voice or "ash", "input": text, "response_format": "mp3"}
    if instructions:
        body["instructions"] = instructions
    r = httpx.post(
        "https://api.openai.com/v1/audio/speech",
        headers={"Authorization": f"Bearer {_key('OPENAI_API_KEY')}"},
        json=body,
        timeout=300,
    )
    if r.status_code != 200:
        raise TTSError(f"OpenAI {r.status_code}: {r.text[:300]}")
    out.write_bytes(r.content)
    return out


def _espeak(text: str, out: Path, *, voice: str) -> Path:
    """Offline robotic placeholder voice, for testing timing without API keys."""
    binary = shutil.which("espeak-ng") or shutil.which("espeak")
    if not binary:
        raise TTSError("espeak-ng not installed (brew install espeak-ng / apt install espeak-ng)")
    subprocess.run([binary, "-v", voice, "-s", "165", "-w", str(out), text], check=True, capture_output=True)
    return out
