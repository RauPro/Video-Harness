---
name: script-writing
description: Write or rewrite the narration script (script.md) for a vh video in the user's voice or a reference creator's voice — hooks, structure, word budget, CTAs. Use before `vh voiceover`, or when the user gives a topic instead of a script.
---

# Script writing

Patterns below come from transcribing the most-viewed videos of each channel (Nov 2026). Data, hooks and links:
`analysis.md` next to this file. Re-measure with `scripts/analyze_scripts.py`.

## Word budget

Measured narration speed (words per minute of speech):

| Voice | wpm | 60 s | 90 s | 3 min |
| --- | --- | --- | --- | --- |
| raul (Spanish) | ~185 | 185 | 280 | 550 |
| luisito (Spanish) | ~167 | 165 | 250 | 500 |
| sam-tyler (English) | ~195 | 195 | 290 | 585 |
| eric-struk (English) | ~245 short / ~220 long | 245 | 370 | 660 |

TTS usually reads 10-15% slower than these creators. When it's TTS, aim about 10% under budget and check the real
length after `vh voiceover`. Speech starts at 0.0 s in every top video: no intro, no greeting, no "hola a todos".

## The hook (first sentence, ≤ 3 s, ≤ 15 words)

Each top video opens with one of these. Pick the one that fits the strongest footage you have:

1. **Outcome first / contradiction.** Show the ending, then rewind. "Así se ve pagar clase ejecutiva para terminar
   con todo roto." → "¿Valió la pena? Te cuento…" (Raul's #1, 538K).
2. **Myth vs. truth question.** "¿Tailandia es realmente tan barato como dicen o es una trampa para turistas?"
   (Raul #2, 225K). Eric: "Would you ever fly the worst airline in the entire world?"
3. **"Así es / Esto es" + superlative.** "Así es viajar en el avión comercial más grande del mundo." / "Esto es el
   Songkran… la batalla de agua más grande del mundo."
4. **Disaster stack (3 things, same day).** "Casi pierdo mi vuelo, pagué cien dólares de multa y mis maletas
   desaparecieron, todo en el mismo día."
5. **Regret / insider tip.** "Ojalá hubiera sabido esto antes de volar con Avianca." Sam: "If you're flying to
   Thailand soon, save this, otherwise you could get a massive headache at immigration."
6. **Place swap.** "Jurassic Park no está en Hollywood, está en Pattaya, Tailandia."
7. **Claim + test (Eric).** "Apparently Canadian money is indestructible, so today we're gonna put it to the test."
8. **Price + place (Luisito/Sam).** "Estos son los cigarrillos de 10 centavos de la India." / "Every single drink
   here is just 20 baht."

Never use generic praise as the hook. "Este es uno de los lugares más impresionantes donde he estado" got the
fewest views (54K) of Raul's top 8. Put a number, a loss, a superlative or a question in the first sentence.

## Structure

**Short (30-90 s):** hook → promise (one line: "te cuento", "3 cosas", "al final te digo…") → 3-5 beats, each with one
concrete fact (price, number, size, time) → twist/payoff → CTA.

**Story / review (2-3 min, Raul's best format):** outcome-first hook → question ("¿Valió la pena?") → route/context
in one sentence ("desde El Salvador hasta Tailandia") → chronological beats with sensory specifics → a comparison
("a diferencia de…", "no es Qatar ni Emirates") → a recurring ritual ("la inspección obligatoria del baño", "activé mi
modo crítico") → twist in the last third → one-line verdict or lesson ("Pequeños detalles que hacen una gran
diferencia.").

**Guide / budget (2-3 min):** myth question → promise + open loop ("Al final te digo el presupuesto para cada tipo de
viajero") → sections by topic (vuelos, alojamiento, comida, tips), each with 2-4 prices → summary by traveler type →
question CTA. Raul's budget video has 7 numbers/min, the most of the 32 analyzed. Numbers are the content; turn each one into a `priceStamp`.

**Eric escalation:** claim + "according to Google" → "You see, normally…" (contrast) → "Right off the bat…" →
"Up next…" → "Now it was time to take this to the next level" → "The final thing…" → one-line conclusion. A sponsor goes
inside a beat, never at the start.

**Luisito explainer:** cold open in the place ("Estar en este país es como…") → history/context → "vean"
(direct address while showing) → local voice/interview → closing reflection on people/humanity ("Parece que la
humanidad es una especie que no aprende de sus errores").

**Sam visual short:** 0-15 words. The footage is the script (top TikToks: 1.6M with one line). Use for
markets, animals, POV. On-screen text carries it; `"captions": {"preset": "none"}` if there is almost no speech.

## Raul's voice (default)

- Spanish, Latino perspective, first person, talks to "tú". Mentions his origin when it adds stakes ("Me vine desde
  El Salvador…", "Si eres latino, prepárate: no existen vuelos directos").
- Short sentences (8-15 words), present tense for action ("Corrí como loco…", "Comenzamos el descenso.").
- Dry nerd humor in one line per video, often math: "la definición gráfica del conjunto vacío", "un conjunto no
  numerable de billetes". Plus self-deprecating asides ("hambre estratégica", "nunca confíen en eso").
- Series continuity: "Si viste mi video anterior…", "pero eso será tema para otro video". 3 of his top 5 are
  replies to a comment ("Replying to @…"). Open with the comment's question when replying.
- Honest verdicts, including negative ones about brands (Avianca). Facts must be checked. Mark any you are not
  sure of with `> verificar:` so the user checks them before publishing.
- CTA: one line, as a question or save/tag: "¿Qué destino debería estar en mi lista? Te leo.", "Guarda este video y
  me lo agradecerás luego.", "Etiqueta a esa persona que está por visitar Tailandia."

## Writing script.md

```markdown
# Hook
Así se ve pagar clase ejecutiva para terminar con todo roto.
[maleta rota, close-up]  ← editing note, not spoken
¿Valió la pena? Te cuento mi travesía desde El Salvador hasta Tailandia.

# Beat 1 — sala VIP
> verificar: precio del boleto
...
```

- One sentence per line. `vh captions` turns lines into phrases, and shots cut on them.
- Write numbers the way they should be said ("mil cuarenta y nueve dólares" if TTS mangles "1049"). Put the
  numeric form in a `[priceStamp $1,049]` note for the timeline.
- Write words to highlight in CAPS in a note (`[highlight: GRATIS]`) → `captions.highlight`.
- Every beat needs footage. Check `vh search` before writing a beat you can't show.

## Checklist before voiceover

- [ ] First sentence has a number, a loss, a superlative or a question, and is ≤ 15 words.
- [ ] Promise or open loop by second 5.
- [ ] One concrete fact per beat. No beat is only adjectives.
- [ ] A twist or surprise in the last third.
- [ ] Word count fits the budget table for the target length.
- [ ] Ends with one CTA line, not three.
- [ ] Facts and prices marked `> verificar:` if unsure.
