# Real-repository pilot, partial results (2026-11-20, still running)

Question: does the closing-line rule (`p3f`) change how many **real** tasks the agent solves, or what it costs? The kits of `../prompt-rules-2026-11-19/` only show whether a model writes the line; this pilot runs the agent on work taken from real repositories.

**What it is.** 20 frozen cases taken from two of the author's repositories (a desktop app and a coding agent): each is a real fixed defect, validated so that its tests fail before the fix and pass after it. The agent gets the report, up to 60 tool calls and a 64,000-token window, one case at a time. A hidden check decides the verdict: `solved`, `overfit` (visible check passes, hidden fails), `blocked`, `budget` (60 tool calls used up before finishing), `failed`, `harness_error`. Control and `p3f` alternate in order, two passes per arm planned, same hardware, LM Studio default KV cache, context 75,008.
**What is not published.** The cases are private code: no case names, tasks or per-case results are in this repository, only the per-pass summaries in the folders next to this file. Those are not enough to rerun the pilot; they are enough to check the totals below with `python3 harness/prompt-rules/pilot_table.py data/real-repo-pilot-2026-11-20`.

## Partial results (as of 2026-11-20 06:00)

| model | pass | solved | verdicts | output tokens | tool calls | seconds |
|---|---|---|---|---|---|---|
| mellum21-q6 | bench-control-r0 | 1/20 | budget 19, solved 1 | 1331712 | 1200 | 12215 |
| mellum21-q6 | bench-p3f-r0 | 4/20 | budget 14, solved 4, blocked 1, failed 1 | 1226512 | 1138 | 11328 |
| oxcoder-q6k | bench-control-r1 | 3/20 | budget 7, overfit 5, blocked 4, solved 3, failed 1 | 282375 | 895 | 4438 |
| oxcoder-q6k | bench-p3f-r1 | 2/20 | budget 11, overfit 3, solved 2, blocked 2, failed 2 | 297071 | 986 | 4851 |
| strata | bench-control-r0 | 8/20 | budget 10, solved 8, overfit 1, failed 1 | 653131 | 1127 | 12038 |
| strata | bench-p3f-r0 | 7/20 | budget 10, solved 7, failed 2, overfit 1 | 601539 | 1103 | 11230 |

Pass names: `-r0` is the first pass, `-r1` the second. A model has an entry only for the passes that finished. **The comparison is not complete for any model**:

- **Strata** (Qwen3.8-Flash-Next IQ3_S, MTP): first pass control 8/20 against `p3f` 7/20, output tokens -7.9 %. Second pass `p3f` was interrupted at 6 of 20 cases and is not counted; second control pass not started. The only model that solves a useful share of the cases.
- **OxCoder 9B Q6_K**: only the second pass of each arm completed (3/20 control, 2/20 `p3f`, tokens +5 %); the first-pass runs have 19 of 20 cases and no summary (the last case could not run, a path missing in one repository snapshot; the runner was fixed afterwards, the first passes were never completed). On the 19 common cases of both passes: 4/38 control, 5/38 `p3f`.
- **Mellum2.1 12B-A2.5B Thinking Q6_K** (no MTP; its MTP load failed): first pass control 1/20 against `p3f` 4/20; it ran out of the tool budget on 19 of 20 cases in control. No second pass.

Reading: for the two small models the share of solved cases is so low (5-20 %) that control against `p3f` cannot be told apart from run-to-run noise (one pass per arm; on Strata only 3 cases are solved by both arms in the first pass, 9 differ in either direction). Work on OxCoder and Mellum was stopped by the owner after these passes because more passes would cost hours of GPU without being able to separate the arms. Strata continues; DaisyRose-27B Q4_K_M is next. This file is updated when passes finish.

## Known quirks

- Two of the 40 Strata runs (one per arm) ended because the model wrote its next tool call as plain text instead of a parsed call (`<tool_call><function=read>...`), which the agent took as its final answer: counted as `failed`, one per arm.
- `budget` is the most frequent verdict on every model (Strata 10 of 20 in both arms). It means unfinished within 60 tool calls, not a wrong answer; where the budget runs out in both arms the closing line has no room to matter.
- The runner crashed at the end of the first OxCoder and Mellum passes because one case's file path did not exist in a repository snapshot; fixed (missing paths skipped, finished cases kept on rerun). The Strata passes ran with the fixed runner.
