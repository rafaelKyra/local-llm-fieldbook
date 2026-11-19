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
Round 6 (four pinned free models) is planned and not yet run; it is not in this folder.

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
