# Reel: Sun 4 Oct 2026, Video 02 "Founders run errands, not businesses"

Source: October Founder Playbook v2.0, section 4, Video 02 (status READY).

| | |
|---|---|
| Account | Founder (Nimra Akbar) |
| Pillar | Identity |
| Post time | **10:30 PM PKT (8:30 PM KSA), tonight, Sun 4 Oct** |
| Length | 29.5 s, 1080x1920, 30 fps, H.264 + AAC, loudness -14 LUFS |
| Video | `out/Nimra_Reel_2026-10-04_Founders_Run_Errands.mp4` |
| Cover | `out/Nimra_Reel_2026-10-04_Cover.jpg` (cover text "Founders run errands.", 3 words) |

## Caption (paste as is)

You started a business, not an admin job. Automate the repeats, keep the decisions. What is your biggest errand right now?

#nimraakbar #aiautomatedmarketer #founderlife #entrepreneurship #aiautomation

## LinkedIn text version (post within 24 hours)

The hook is the first line, then one script line per row, and the closing question comes last. It uses 3 hashtags.

```
Founders don't run businesses. They run errands.

Answer DMs. Send invoices. Chase leads.
That is not leadership. That is admin with a nicer title.
Every errand hour is an hour not spent growing.
Automate the repeats. Keep the decisions.

Be honest: what is your biggest errand right now?

#founderlife #aiautomation #entrepreneurship
```

## Script on screen and in the voice-over (word for word from the card)

| Time | Line |
|---|---|
| 0.25 s | Founders don't run businesses. They run errands. *(hook on screen in under 2 s)* |
| 4.1 s | Answer DMs. Send invoices. Chase leads. |
| 8.45 s | That is not leadership. That is admin, with a nicer title. |
| 12.85 s | Every errand hour is an hour not spent growing. |
| 16.05 s | Automate the repeats. Keep the decisions. |
| 19.85 s | Be honest. What is your biggest errand right now? |
| 23.5 s | Logo lock-up |

## Pre-publish checklist (playbook section 5)

- [x] Tagged to one account (founder). Not a duplicate of a company post.
- [x] Hook on screen in the first two seconds.
- [x] Every spoken line is on screen as kinetic text.
- [x] Cover text is 5 words or fewer, in brand colours only.
- [x] No placeholders, no numbers, no prices, no client names on screen.
- [x] No emoji, no DM keyword, no hard call to action. Closes with a question.
- [x] No "I" statements, so the truth check passes as written.
- [ ] Caption, hashtags and link in bio set.
- [ ] LinkedIn text version scheduled within 24 hours.
- [ ] After posting: answer comments within 2 hours (7 PM to 1:30 AM window). Note the first-hour result for Friday's review.

## Production notes

- **Voice-over** is a neural AI voice (Kokoro, voice `af_heart`), not Nimra's own voice. To use her real voice,
  record the 11 lines in `audio/tts.py` as separate WAVs, replace the files in `audio/vo/`, and run
  `python3 audio/mix.py`. Then run the final `ffmpeg` step in `build.sh`. Each line has some slack before the next one starts.
- **Colours**: background cream `#F7F3EC`, maroon `#63080F`, green `#043417` (the brand green from the playbook,
  which matches the logo; the `#4D0C12` in the brief is a dark burgundy, not a green).
- **Music and sound effects** are synthesized from scratch in `audio/mix.py`, so they are royalty-free and contain no samples.
- **Rebuild everything**: `./build.sh` (Node 18+, Python 3 with numpy, scipy and soundfile, and ffmpeg).
