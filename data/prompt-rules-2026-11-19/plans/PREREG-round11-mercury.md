# Round 11 plan: Mercury 3, a serious confirmation (written 2026-11-20 BEFORE any run; not yet started, waits for the owner's Inception key)

Why: Mercury 3 (`mercury-3`, Inception API, direct, not on OpenRouter) is the model with the strongest early evidence for the closing-line rule (kit P3b, round 2: 29/30 with `p3f` against 22/30 control, `finish`-tool wording) but (a) the kit P3c, where the effect shows without a ceiling, was never run on it; (b) its bench control came from another round, so the cost figure (about -3 %) is not a controlled comparison; (c) it is the only capable model whose 38-task bench is below the ceiling (36-37 of 38), so solved counts can move there.

Same agent, kits, hidden checks, arm texts and window (64,000) as rounds 3-7; fixed id `mercury-3`; temperature as the endpoint default; concurrency 1 throughout (the earlier Mercury rounds used 4), so that the arms alternate in strict order as in round 7.

## Part A: kits (primary question)
- Kits P3b and P3c, arms control and `p3f`, 32 repetitions per kit and arm (128 runs), order alternating by repetition.
- **Primary test (one, so no correction):** P3c closing line, `p3f` against control, Fisher exact two-sided, claim at p < 0.05.
- Secondary (reported, not claimed): P3b closing line; solved per kit; output tokens per run (ratio of means with bootstrap 95 % interval).
- Interrupted runs (endpoint error, rate limit) are moved aside and redone, never counted (fieldbook CORRECTIONS 11).

## Part B: bench (cost and safety)
- 38-task bench, control against `p3f`, 4 passes each, alternating order, same session and window, seed offsets 0-3.
- **Safety criterion (fixed now):** `p3f` is acceptable only if its solved total over the 4 passes is no more than 3 below control (of 152), and the share of runs with the `finish` tool misused does not rise.
- **Cost criterion:** output tokens `p3f` / control with a bootstrap 95 % interval; a result is called an increase only if the interval excludes 1. The screen-A rule (reject above +10 % output cost with no more solved) is applied as written, and any deviation is recorded as one.

## Stopping
Spend cap set by the owner (estimate below); the driver reads the endpoint's usage if available, otherwise estimates from token counts, and stops at the cap. Nothing in this plan changes after the first run; anything added later is labelled exploratory.

## Estimate (list price $0.20 input / $0.70 output per M tokens; sources disagree, a launch price of half that is reported)
Kits: about 4.1 M input + 0.45 M output tokens = about $1.1. Bench: 8 passes of about 0.7 M input + 50 k output = about $1.4. Total about $2.5 (about $1.3 at the reported launch price). Not confirmed against the account.
