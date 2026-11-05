# Key findings

- **Raul (@raul.guillen.h):** the top 2 (538K, 225K) are 2-3 min, Spanish, ~185 wpm. Each opens with a contradiction or
  myth question and has dense numbers (2-7/min; Eric and Luisito ≤3, Sam's tip TikToks 5-6). 3 of the top 5 are replies to comments, and the Avianca → A380 →
  Songkran → budget videos form a series. The weakest of the top 8 opens with generic praise (Prague, 54K).
- **Eric Struk:** 245-285 wpm on Shorts. Formula: claim + "according to Google" + test, then "You see, normally" contrast,
  an escalation ladder of tests, a one-line conclusion, and a sponsor inside a beat.
- **Luisito:** ~167 wpm. Cold open in the place, a price + place first line, "vean", local interviews, and a closing
  moral reflection. Some top Shorts are pure sketches or reactions.
- **Sam Tyler:** the top TikToks are visual with 0-15 words (1.6M, 1.2M). The talking ones are save-this tips ("3 things")
  and price-led discoveries. Long-form opens on the best interview soundbite.

# Top-video script analysis

Most-viewed videos per channel, pulled with yt-dlp in Nov 2026 and transcribed with faster-whisper `small`.
Long-form videos are only the first 4 min. wpm = words per minute of speech. Numbers/min counts each amount (`$500`, `99 baht`, `1049`) or spoken price word once. Numbers that Whisper
writes as words ("cien") are only counted when a currency word follows, so these are lower bounds.
Whisper punctuation is unreliable, so don't trust sentence-length figures. Regenerate with `scripts/analyze_scripts.py`.

| Video | Views | Length | wpm | Numbers/min | Opening (first 3 s) |
| --- | --- | --- | --- | --- | --- |
| [eric-struk short](https://www.youtube.com/shorts/B-jVze9aGyo) | 41,000,000 | 45s | 248 | 0.0 | Apparently, Canadian money is indestructible, so today we're gonna put |
| [eric-struk short](https://www.youtube.com/shorts/HUJxSWeSqPE) | 25,000,000 | 49s | 230 | 1.2 | I've put the best gaming setup in the entire world. |
| [eric-struk short](https://www.youtube.com/shorts/UTAtldfvkKo) | 24,000,000 | 47s | 263 | 0.0 | Today I tried one of the most unique ice cream places in the entire world. |
| [eric-struk short](https://www.youtube.com/shorts/78xYljhwndk) | 14,000,000 | 41s | 225 | 1.7 | This is my mom and this is a self -driving car so |
| [eric-struk short](https://www.youtube.com/shorts/enk_PsqfK0s) | 13,000,000 | 53s | 284 | 2.3 | Today I was at home going through some of my old stuff when I found my old iPhone 12, |
| [eric-struk long](https://www.youtube.com/watch?v=nQggQr_iSg4) | 3,300,000 | 240s | 225 | 1.0 | Would you ever fly the worst airline in the entire |
| [eric-struk long](https://www.youtube.com/watch?v=_lAIcDy9Bc8) | 2,600,000 | 240s | 220 | 1.3 | K -pop fans scare me these people will do anything to |
| [luisito long](https://www.youtube.com/watch?v=69qKUoGhoQo) | 72,000,000 | 240s | 157 | 1.0 | A continuación, entraremos a una celda de aislamiento que es a donde los |
| [luisito short](https://www.youtube.com/shorts/7godoItuG_Q) | 45,000,000 | 25s | 92 | 0.0 | una demostración de cómo cuando |
| [luisito short](https://www.youtube.com/shorts/o3xC6xROIVk) | 45,000,000 | 59s | 184 | 3.1 | Estos son los cigarrillos de 10 centavos de la India |
| [luisito long](https://www.youtube.com/watch?v=MJR3YbsJ5oU) | 42,000,000 | 240s | 179 | 0.3 | Estar en este país es como dar un viaje décadas en el pasado. |
| [luisito short](https://www.youtube.com/shorts/Bl06vBMQEn4) | 28,000,000 | 41s | 150 | 2.9 | Recientemente, visite las oficinas de YouTube y me |
| [luisito short](https://www.youtube.com/shorts/P4Gv8GYaevU) | 12,000,000 | 48s | 196 | 0.0 | En este punto de Nagasaki Japón fue que cayó la segunda bomba |
| [luisito short](https://www.youtube.com/shorts/uiX-8X-e61w) | 12,000,000 | 49s | 142 | 0.0 | Traten de seguirme. Pero no cambiaste lo que tienes ahí |
| [raul tiktok](https://www.tiktok.com/@raul.guillen.h/video/7584519537672850744) | 538,200 | 122s | 191 | 2.6 | Así se ve para dar primera clase, para terminar con todo roto. |
| [raul tiktok](https://www.tiktok.com/@raul.guillen.h/video/7606367471553105170) | 225,100 | 183s | 170 | 7.0 | Tailandia es realmente tan barato como dicen o es |
| [raul tiktok](https://www.tiktok.com/@raul.guillen.h/video/7587139185715252488) | 136,600 | 94s | 164 | 1.9 | Esto es |
| [raul tiktok](https://www.tiktok.com/@raul.guillen.h/video/7584873553032465675) | 106,000 | 164s | 185 | 2.2 | Así es viajar en el avión comercial más grande del mundo. |
| [raul tiktok](https://www.tiktok.com/@raul.guillen.h/video/7585639313308683576) | 104,000 | 43s | 200 | 2.9 | Ojalá hubiera sabido esto antes de volar con Avianca. |
| [raul tiktok](https://www.tiktok.com/@raul.guillen.h/video/7584108727297412364) | 58,000 | 87s | 190 | 2.1 | Casi pierdo mi vuelo, pague cien dólares de multa y |
| [raul tiktok](https://www.tiktok.com/@raul.guillen.h/video/7583463423737122060) | 54,500 | 138s | 166 | 1.7 | Este es uno de los lugares más impresionantes donde he |
| [raul tiktok](https://www.tiktok.com/@raul.guillen.h/video/7587903600563588408) | 48,500 | 37s | 194 | 3.4 | Jurassic Park no está en Hollywood, está en Pataya, Tailandia. |
| [sam-tyler short](https://www.youtube.com/shorts/mr0n3EQVz_s) | 6,100,000 | 86s | 160 | 0.7 | Right behind me is the biggest squishy market in Thailand. |
| [sam-tyler tiktok](https://www.tiktok.com/@thesamtyler/video/7700930960283553030) | 1,600,000 | 14s | 78 | 0.0 | Hello, look at this, hello, |
| [sam-tyler tiktok](https://www.tiktok.com/@thesamtyler/video/7674206427036011797) | 1,200,000 | 25s | 182 | 5.0 | just found the cutest hidden cafe in |
| [sam-tyler tiktok](https://www.tiktok.com/@thesamtyler/video/7683487118378814741) | 1,200,000 | 47s | 25 | 0.0 | Thank |
| [sam-tyler short](https://www.youtube.com/shorts/nCyIgA7UMYM) | 764,000 | 115s | 228 | 1.0 | Excuse me, do you live here in Bangkok? You're just traveling here. Yeah, I live here in |
| [sam-tyler long](https://www.youtube.com/watch?v=pkVuSc8BH4w) | 756,000 | 240s | 208 | 2.0 | It feels like a penthouse, so it's an older building but |
| [sam-tyler long](https://www.youtube.com/watch?v=alBEVgDlv-I) | 701,000 | 240s | 186 | 3.5 | So anyone watching, you cannot own land in Thailand. |
| [sam-tyler tiktok](https://www.tiktok.com/@thesamtyler/video/7675709658136317204) | 675,500 | 60s | 233 | 6.0 | if you're flying to Thailand soon save this otherwise you could get a massive |
| [sam-tyler short](https://www.youtube.com/shorts/WdBKkrXaK-E) | 632,000 | 19s | 79 | 0.0 | Thailand |
