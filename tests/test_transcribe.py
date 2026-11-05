from vh.transcribe import align_to_script, narration_from_script, phrases, plain_text, speech_regions


def w(text, s, e):
    return {"text": text, "startMs": s, "endMs": e, "timestampMs": (s + e) // 2, "confidence": 0.9}


def test_narration_strips_directions():
    script = "# Title\n[HOOK: text]\nHola mundo.\n> note\n<!-- c -->\n- Dos cosas [b-roll]\n"
    assert narration_from_script(script) == "Hola mundo. Dos cosas"


def test_align_keeps_timing_uses_script_spelling():
    words = [
        w(" vivir", 0, 300),
        w(" en", 300, 400),
        w(" bankok", 400, 900),
        w(" eh", 900, 1000),
        w(" 500", 1000, 1400),
    ]
    out = align_to_script(words, "Vivir en Bangkok $500.")
    assert plain_text(out) == "Vivir en Bangkok $500."
    assert out[0]["startMs"] == 0 and out[-1]["endMs"] == 1400
    assert all(a["endMs"] <= b["startMs"] for a, b in zip(out, out[1:], strict=False))


def test_phrases_and_regions():
    words = [w("Uno,", 0, 200), w(" la", 250, 400), w(" renta.", 400, 800), w(" Dos", 2000, 2300)]
    ph = phrases(words)
    assert [p["text"] for p in ph] == ["Uno,", "la renta.", "Dos"]
    assert speech_regions(words) == [[0, 920], [1880, 2420]]
