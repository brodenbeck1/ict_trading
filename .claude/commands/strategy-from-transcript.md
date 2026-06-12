# Strategy From Transcript

Extract a structured trading strategy from a YouTube transcript or pasted text.

**Usage:**
- `/strategy-from-transcript` then paste the transcript in your next message
- `/strategy-from-transcript <YouTube URL>` to fetch automatically (requires yt-dlp or youtube-transcript-api)
- `/strategy-from-transcript <pasted transcript text>`

## Instructions

You are helping document a futures trading strategy from a YouTube video or transcript for the ICT Trading project. Your job is to extract the rules precisely and produce a structured notes file — **no code**, just clear rules that can later be turned into a model.

### Step 1 — Get the transcript

If `$ARGUMENTS` is a YouTube URL:
- Try: `python3 -c "from youtube_transcript_api import YouTubeTranscriptApi; import re; vid=re.search(r'v=([^&]+)', '$ARGUMENTS').group(1); t=YouTubeTranscriptApi.get_transcript(vid); print(' '.join([x['text'] for x in t]))"`
- If that fails, tell the user the package is missing and ask them to paste the transcript manually.

If `$ARGUMENTS` is pasted text (or no argument), use it directly as the transcript.

### Step 2 — Analyze the transcript

Read the full transcript carefully. Identify:

1. **Strategy name** — what the creator calls it, or a descriptive name you infer
2. **Instrument(s)** — which markets (ES, NQ, YM, or others)
3. **Timeframes** — which chart timeframes are used (entry TF, bias TF, confirmation TF)
4. **ICT concepts involved** — from: FVG, SMT divergence, stop hunt/liquidity sweep, draw on liquidity, market structure shift, session liquidity pools, OHLC/OLHC expectation, OTE retracement, breaker blocks, order blocks, displacement, etc.
5. **Sequential entry checklist** — ordered list of conditions that must ALL be true to take a trade
6. **Entry trigger** — exactly what candle/condition starts the trade
7. **Stop placement** — where the stop loss goes
8. **Target(s)** — where the take profit goes (liquidity level, FVG, fixed R, etc.)
9. **Filters** — what disqualifies a setup (news, time of day, session, missing component)
10. **Edge/thesis** — why this setup has an edge (the market logic behind it)
11. **Open questions** — anything ambiguous or unstated in the transcript that needs clarification before coding

### Step 3 — Write the notes file

Determine a short kebab-case strategy name (e.g., `london-fvg-sweep`, `ny-smt-reversal`).

Write the output to: `trading_models/strategies/notes/<strategy-name>.md`

Create the directory if it doesn't exist: `mkdir -p trading_models/strategies/notes`

Use this exact template:

```markdown
# Strategy: <Full Strategy Name>

**Source**: <YouTube URL or "transcript pasted by user">
**Date extracted**: <today's date>
**Status**: Notes only — not yet coded

---

## Overview

<2-3 sentence summary of what the strategy is and why it works>

## Instruments

<Which futures instruments. Note which is primary and which are used for SMT.>

## Timeframes

| Role | Timeframe |
|---|---|
| Bias | e.g. Daily |
| Context | e.g. 4H |
| Entry | e.g. 5m |

## ICT Concepts Used

- <concept 1>
- <concept 2>
...

## Entry Checklist (all must be true)

1. <First condition — bias/context level>
2. <Second condition>
3. ...
n. <Final trigger>

**Entry**: <exactly when/where to enter>

## Stop Loss

<Where the stop goes and why>

## Targets

1. <First target — nearest liquidity>
2. <Second target — if applicable>

## Session / Time Filters

<When to trade, when not to trade>

## Filters (Rule of Exclusion)

- <What disqualifies the setup>
- ...

## Edge / Thesis

<Why this setup has an edge — the market microstructure logic>

## Open Questions

- [ ] <Anything unclear that needs clarification before coding>
- [ ] ...

## Notes

<Any other observations from the transcript>
```

### Step 4 — Confirm with the user

After writing the file, tell the user:
- The file path where notes were saved
- A brief summary of the strategy (2-3 sentences)
- The open questions list so they can answer before you build code
- Ask: "Ready to scaffold the model class, or do you want to refine the rules first?"
