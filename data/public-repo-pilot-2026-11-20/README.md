# Public-repository pilot on Mercury 3 (2026-11-20)

Question: does the closing-line rule (`p3f`) lose or cost anything on **real** repair work, with cases that can be published? The private pilot (the author's own repositories) cannot be sent to a provider that trains on prompts (Inception), so 20 cases were built from six **public** GitHub repositories (fb55/htmlparser2, felladrin/MiniSearch, dyoshikawa/rulesync, nansen-ai/nansen-cli, agentclientprotocol/claude-agent-acp, solidjs/solid-router), all fix commits dated on or after 2026-09-15.

**How the cases were made** (scripts in `cases/`): `scan_public.py` finds fix commits with changed tests and 1-3 source files (826 candidates); `validate_public.mjs` runs the project's own tests on the parent and on the fix, twice each (the fix's tests must fail on real assertions on the parent and pass on the fix: 54 of 74 sampled candidates valid); missing-symbol failures are dropped (50 fair); 20 are chosen by sha256 order with a quota per repository; the symptom reports were written by hand from the observed failure and the behaviour the tests demand (`make_cases.py`; no commit message, test name or fix code). `cases/PUBLIC-FROZEN.md` holds the sha256 of `tasks-public.mjs`. The plan, with the safety criterion, was written before the first run: `PREREG-round13-public-pilot.md`.

**Setup:** Forge agent, Mercury 3 (`mercury-3`, Inception API), window 64,000, at most 60 tool calls per case, concurrency 1, control (`dist/lib.js`) and `p3f` (`dist-finish/lib.js`), 2 passes per arm in alternating order. The agent sees the repository at the parent of the fix and the report; a hidden run of the fix's test files decides the verdict.

## Result (`RESULT.md`, from `python3 harness/prompt-rules/public_pilot_table.py data/public-repo-pilot-2026-11-20`)

| | control | `p3f` |
|---|---|---|
| solved (40 case-runs) | 34 | 36 |
| passes | 17, 17 | 18, 18 |
| budget (60 calls used) | 6 | 4 |
| output tokens | 817,931 | 739,743 |
| input tokens | 33.5 M | 29.8 M |

`p3f` 36/40 against control 34/40 (Fisher p = 0.74); paired by case and pass both 33, neither 3, only `p3f` 3, only control 1 (sign test p = 0.63); 2 of 20 cases changed outcome between the two passes in either arm (the runs are stable). Output tokens `p3f` / control 0.90 (per-case bootstrap 95 % 0.73-1.12), input tokens 0.89, wall time 0.84. **The safety criterion fixed beforehand (`p3f` not more than 3 below control) is met with room to spare, and there is no cost increase.** With 40 case-runs per arm only a large loss could have been seen; no loss was seen.

## What went wrong on the way (and how it was handled)

- **Endpoint failure in the first control r1 pass:** from 12:27 every remaining case ended in seconds with "model kept returning empty replies" (13 cases verdict `blocked`, 1 `solved` with status blocked: 14 rows), while the first seven cases had run normally and the API answered a probe normally afterwards. These are failures of the endpoint, not outcomes of the agent, so the 14 rows were moved to `endpoint-failures/` (with the first attempt's summary, 6/20 solved, 13 blocked) and never counted, and the pass was rerun for those cases only (the six finished cases were kept). The rerun produced no empty reply. This is the same rule as for interrupted runs (CORRECTIONS 11); note that only this specific stop reason, together with its sudden onset for every case, was treated as an endpoint failure; `budget`, `unverified` and `blocked` for other reasons remain real outcomes (CORRECTIONS 13).
- **Cap:** the plan said 10 USD estimated (token counts at list price 0.20 / 0.70 USD per M, no cache discount, so an upper bound; the real bill was not visible). The driver checks the cap only before a pass starts and would have started the last pass above it, so it was stopped, the owner was asked, and the last pass ran with a raised cap of 14 USD on the owner's yes. Final estimate 13.74 USD.
- **Limits:** the public repositories can be in the model's training data (the date filter is the only protection); several reports carry exact strings taken from the tests because the behaviour cannot be stated without them; one model, one run family, 20 cases, two passes.

Context: on the private pilot with Strata the same comparison went the other way (12/40 against 17/40, p = 0.35); the discordant case-run pairs of all four real-work comparisons together (Strata private pilot 10 lost and 5 gained, Mercury bench 5 and 2, deepseek bench 4 and 2, this pilot 1 and 3) are 20 lost and 12 gained (sign test p = 0.22), which is no evidence of a loss either way.
