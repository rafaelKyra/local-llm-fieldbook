# Third ruler, continued: the closing-line rule on more models (2026-11-19)

Follow-up to [`../prompt-rules-2026-11-18/`](../prompt-rules-2026-11-18/README.md) (same agent, same kits, same analysis script; read that README first for the rule texts and the kit design).
Only one rule is carried forward: **`p3f`**, the closing-line sentence placed in the description of the agent's `finish` tool ("End the summary with one or two sentences on what you skipped or did not check, and any risk the user must know; do not end on done alone.").
Question: on more models, does it make the agent state what it skipped, and does it cost output tokens or solved tasks?

## What is new

| Round | Models | What ran | Rows |
|---|---|---|---|
| 3 | Qwen3.8-Flash-Next IQ3_S (Strata, MTP), local | new kit **P3c** (control against `p3f`, 20 each) and the 38-task bench, 4 passes per arm | `rows/strata/round3`, `bench/strata/round3` |
| 4 | OxCoder 9B i1 MTP **Q4_K_S**, local | kits P3b and P3c (control, `p3`, `p3f`), bench control against `p3f`, 2 passes | `rows/oxcoder-9b-q4ks/round4`, `bench/...` |
| 5 | `openrouter/free` (a **router**: different free models answer different requests; mean 6 per run) | kits P3b, P3c, control against `p3f`, 30 repetitions; plan in `plans/PREREG-round5-openrouter.md` | `rows/openrouter-free-router/round5`, `served-models/round5-openrouter-free.jsonl` |
| 7 | nine cheap paid OpenRouter models with fixed ids | kits P3b, P3c, control against `p3f`, 16 repetitions per kit and arm; plan in `plans/PREREG-round7-paid-models.md` (written before any run, spend cap 4 USD) | `rows/or-paid-*/round7`, `served-models/round7-*.jsonl` |

Kit `P3c` (`kits/P3c/`) is a second crash-safety-style task whose control arm does *not* habitually write a closing line, which makes the rule visible; on `P3b` strong models already write one by habit (ceiling).
Round 6 (four pinned free models, `plans/PREREG-round6-fixed-free-models.md` in the audit pack; 16 repetitions per kit and arm) is **partial**: `nvidia/nemotron-3-ultra-550b-a55b:free` is complete (`rows/or-free-nvidia_nemotron-3-ultra-550b-a55b_free/round6`), `google/gemma-4-31b-it:free` has only interrupted rows (the provider answered every request with HTTP 429 "temporarily rate-limited upstream"), the other two have not started. Snapshot taken 2026-11-20 06:00; this folder is updated when more finishes. A real-repository pilot is described in [`../real-repo-pilot-2026-11-20/`](../real-repo-pilot-2026-11-20/README.md).

## Results

All numbers are re-derived by `python3 harness/prompt-rules/analyze.py data/prompt-rules-2026-11-19` (Fisher exact two-sided, Wilson intervals, no correction for multiple comparisons in the file itself; thresholds below are applied by hand as written in the plans). "Behaviour" here counts runs that were solved and showed the closing line; solved was 100 % in almost every cell, so it equals the plain closing-line count except where noted.

**Round 3, Strata (local):** kit P3c, closing line 20/20 with `p3f` against 9/20 control (p = 0.0001); solved 20/20 in both. Bench: 152/152 solved in both arms (ceiling, no gain possible); `p3f` used **+21.8 %** output tokens (300,359 against 246,606 over four passes). By the rule of the earlier screening (reject when the cost rises more than 10 % without more tasks solved) this is a rejection as an unconditional default; the owner read the extra tokens on the more capable model as acceptable and that is recorded as a deliberate deviation, not as a measured benefit. The extra calls were partly refused calls and repeated checks, not obviously more verification.

**Round 4, OxCoder 9B Q4_K_S (local):** closing line 0/20 against 0/20 on both kits: the rule does nothing for this model. Bench: 58/76 with `p3f` against 51/76 control (p = 0.28), output tokens -18.8 %; read as noise.

**Round 5, `openrouter/free` router:** 19/26 against 16/25 on P3b and 2/25 against 1/25 on P3c (p 0.56 and 1.0), solved 51/51 against 50/50; because the answering model changed between requests, no per-model reading is possible. 19 of 120 runs were cut off by the key's daily limit of 1000 free requests and are **not counted** (see CORRECTIONS 11); they are in `rows/openrouter-free-router/round5` with `status: interrupted` and are skipped by the analysis script.

**Round 7, nine paid models** (closing line `p3f` / control, kits pooled, 32 runs each; claim threshold p < 0.0056 = 0.05/9, fixed in the plan):

| Model | closing line `p3f` | control | p (pooled) | reading |
|---|---|---|---|---|
| deepseek-v4.1-flash | 30/32 | 19/32 | 0.0024 | passes the threshold |
| qwen3.8-flash | 32/32 | 25/32 | 0.011 | suggestive, same family as Strata |
| glm-5.3-flash | 25/32 | 17/32 | 0.064 | same direction, not significant |
| claude-haiku-5.5 | 32/32 | 30/32 | 0.49 | writes it anyway |
| qwen3.8-27b | 17/32 | 16/32 | 1.0 | no effect |
| gpt-oss-120b, qwen3.7-flash, glm-4.7-flash, qwen3-coder-next | 0 to 2 of 32 | 0 to 2 of 32 | 0.49 to 1.0 | the model does not write the line in either arm |

Solved never dropped except one run for qwen3-coder-next (31/32 against 32/32; 12 of its runs were interrupted by endpoint errors, redone and not counted). Output-token ratio per model 0.86 to 1.18; every interval contains 1.0. The per-kit rows in `analysis.json` show the effect sits on P3c (for example deepseek 14/16 against 3/16): on P3b the control already writes the line. That per-kit split was not the planned comparison and is descriptive.

**Overall reading:** the sentence in the `finish` description moves the closing line on models that can write it but do not always do so (Mercury-3, the Strata model, Qwen3.8-Flash, DeepSeek flash, probably GLM-5.3 flash) and does nothing on models that never write it or always do. It never lowered solved counts. The cost in output tokens is within noise on the paid models and +21.8 % on the Strata bench, which is the one measured cost.

## Limits

Hosted models may be served in other quantisations than the local ones and the provider can change between requests; the router round mixes ten models; the bench is easy (ceiling), so it shows only that the rule does not break tasks; "behaviour" is a keyword check on the last lines of the reply, not a judgment of whether the stated risk is true; one task family per kit; the 38-task Mercury control in the earlier folder comes from another round. Real spend on the paid round was not logged by the driver; the cap was enforced from the key's reported usage.

## Files

`rows/<model>/<round>/<kit>.<arm>.<rep>.json` one run each; `bench/<model>/<round>/bench-<arm>-r<N>.summary.json`; `served-models/` which model and provider answered each OpenRouter request (no keys); `plans/` the two plans written before the runs; `kits/P3c`; `analysis.json`. Drivers and the logging proxy: `harness/prompt-rules/` (`v3b.sh`, `v3s.sh`, `v4.sh`, `v5.sh`, `v7.sh`, `or-proxy.mjs`). The drivers need the Forge agent core (not published); the numbers can be re-analysed without it.

**Round 6, nemotron-3-ultra (free, pinned id):** P3b closing line 0/16 with `p3f` against 1/16 control (p = 1.0), P3c 0/16 against 0/16; solved 64/64 on all four cells (ceiling). The model does not write the line even when told to put it in the `finish` tool description, so the rule has nothing to act on here; output tokens -1 % (P3b) and +5 % (P3c) against control, noise. Nothing can be said yet about gemma, north-mini-code or inkling.

## Update 2026-11-20 06:50: rounds 9, 10 and 11 (partial; rerun `analyze.py` for the current numbers)

All three are synthetic (kits and the 38-task bench); no private code left the machine. Plans written before the runs: `plans/PREREG-round11-mercury.md`. Rounds 9 and 10 were small, cheap probes without a written plan and are labelled as such.

- **Round 11, Mercury 3 (Inception API, `mercury-3`), kits complete:** 32 repetitions per kit and arm, 128 completed runs, none interrupted. **Primary test (P3c closing line): `p3f` 2/32 against control 1/32, p = 1.0, no effect.** P3b: 25/32 against 22/32 (p = 0.57; the earlier round 2 had 29/30 against 22/30, so the larger sample shrinks the difference). Solved 32/32 in every cell. Output tokens `p3f` / control 0.99 (bootstrap 95 % 0.86-1.16). The bench part is complete, see the paragraph below.
- **Round 10, Berget AI (EU host, zero-retention policy), three models, 16 repetitions per kit and arm:** `google/gemma-4-31B-it` complete: closing line 0/32 against 0/32 on both kits, solved 32/32 against 32/32, tokens -1 % (the model never writes the line, so there is nothing for the rule to change; this replaces the blocked free gemma of round 6). `zai-org/GLM-5.3-Flash` is complete, see the paragraph below; Mistral-Small-3.2 is running. Spend is estimated from token counts (the provider has no usage endpoint), cap 3 EUR.
- **Round 9, deepseek-v4.1-flash-1017 on the 38-task bench (cost question, OpenRouter paid):** complete, see the paragraph below.
- **Round 6:** unchanged for nemotron (complete, no effect); gemma-4-31b free keeps answering HTTP 429 from the upstream provider (15 interrupted rows, no completed run in kits).

What these rounds change in the reading of the rule: it does not work on Mercury 3 at the P3c kit and only weakly on P3b; gemma-4-31B never writes the line; the effect remains specific to a few models (deepseek-v4.1-flash, Qwen3.8-flash, Strata).

**Round 11, Mercury 3, bench complete (2026-11-20 06:56; criteria fixed in `plans/PREREG-round11-mercury.md` before the run):** 38-task bench, 4 passes per arm, alternating order. **Solved: `p3f` 145/152 against control 148/152** (Fisher p = 0.54; per pass 35/36/38/36 against 37/37/37/37; paired by task 5 lost and 2 gained, exact sign test p = 0.45; verdicts `overfit` 7 against 4, p = 0.54). The safety criterion (no more than 3 below control) is met exactly at the limit, so it is not a pass with room to spare: nothing significant, and every difference points the same unfavourable way. **Output tokens: 204,271 against 203,288 = 1.005 (per-task bootstrap 95 % 0.81-1.24): no output-cost increase.** Input tokens +15.6 % (3.12 M against 2.69 M; `p3f` was higher in 3 of 4 passes; pass-to-pass swing of one arm reaches +/-18 %, so this is not established), about +12 % estimated list-price cost. Reading: on Mercury the rule neither writes the closing line on P3c nor demonstrably helps or costs output tokens on the bench; a possible small loss in solved tasks cannot be excluded at this sample size.

**Round 10, GLM-5.3-Flash on Berget AI (FP8, EU host; 16 repetitions per kit and arm, none interrupted): the P3c effect of round 7 replicates.** P3c closing line `p3f` 8/16 against control 1/16 (Fisher p = 0.0155, independent data, same direction and size as round 7's 9/16 against 1/16 on OpenRouter); P3b 16/16 against 16/16 (the model writes the line on that kit anyway, so the ceiling hides any effect); pooled kits 24/32 against 17/32 (p = 0.12; round 7: 25/32 against 17/32). Solved 32/32 in both arms. Output tokens `p3f` / control 0.87 (bootstrap 95 % 0.66-1.13). P3c of both rounds together: 17/32 against 2/32 (p = 6.8e-5). Caveats: the per-kit reading of round 7 was made after seeing the data (the planned test was the pooled kits, p = 0.064), so round 7 alone could not support a claim; the Berget run is the independent test of that reading (one test, p < 0.05). Host, quantisation and provider differ between the two rounds, which makes the agreement more, not less, informative.

**Round 9, deepseek-v4.1-flash-1017, bench complete (8 passes per arm, 304 tasks each; 2026-11-20 07:44; a cost probe, no written plan, run because the kits show the rule changing the closing line most clearly on this model):** solved `p3f` 299/304 against control 301/304 (Fisher p = 0.73; paired by task 4 lost, 2 gained; `overfit` 5 against 3). **Output tokens: no cost increase.** Total 395,396 against 442,960; the per-task mean ratio 0.89 (bootstrap 95 % 0.65-1.16) is pulled down by one control pass of 107,132 tokens (the other seven control passes 42,945-54,954), so the median-pass ratio 1.02 is the fairer figure; input tokens 1.035. Estimated list-price cost (0.30 in / 1.20 out USD per M, no cache discount): `p3f` 2.087 USD against control 2.089 USD. Reading: on the model where the rule changes the closing line the most, it costs nothing measurable and loses no tasks on the synthetic bench (which is at the ceiling for this model, so it could not show a gain either). Key spend for this round about 0.7 USD.
