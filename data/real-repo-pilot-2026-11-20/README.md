# Real-repository pilot, partial results (2026-11-20, still running)

Question: does the closing-line rule (`p3f`) change how many **real** tasks the agent solves, or what it costs? The kits of `../prompt-rules-2026-11-19/` only show whether a model writes the line; this pilot runs the agent on work taken from real repositories.

**What it is.** 20 frozen cases taken from two of the author's repositories (a desktop app and a coding agent): each is a real fixed defect, validated so that its tests fail before the fix and pass after it. The agent gets the report, up to 60 tool calls and a 64,000-token window, one case at a time. A hidden check decides the verdict: `solved`, `overfit` (visible check passes, hidden fails), `blocked`, `budget` (60 tool calls used up before finishing), `failed`, `harness_error`. Control and `p3f` alternate in order, two passes per arm planned, same hardware, LM Studio default KV cache, context 75,008.
**What is not published.** The cases are private code: no case names, tasks or per-case results are in this repository, only the per-pass summaries in the folders next to this file. Those are not enough to rerun the pilot; they are enough to check the totals below with `python3 harness/prompt-rules/pilot_table.py data/real-repo-pilot-2026-11-20`.

## Results (Strata complete 2026-11-20 10:17; OxCoder and Mellum partial, stopped)

| model | pass | solved | verdicts | output tokens | tool calls | seconds |
|---|---|---|---|---|---|---|
| mellum21-q6 | bench-control-r0 | 1/20 | budget 19, solved 1 | 1331712 | 1200 | 12215 |
| mellum21-q6 | bench-p3f-r0 | 4/20 | budget 14, solved 4, blocked 1, failed 1 | 1226512 | 1138 | 11328 |
| oxcoder-q6k | bench-control-r1 | 3/20 | budget 7, overfit 5, blocked 4, solved 3, failed 1 | 282375 | 895 | 4438 |
| oxcoder-q6k | bench-p3f-r1 | 2/20 | budget 11, overfit 3, solved 2, blocked 2, failed 2 | 297071 | 986 | 4851 |
| strata | bench-control-r0 | 8/20 | budget 10, solved 8, overfit 1, failed 1 | 653131 | 1127 | 12038 |
| strata | bench-p3f-r0 | 7/20 | budget 10, solved 7, failed 2, overfit 1 | 601539 | 1103 | 11230 |

Pass names: `-r0` is the first pass, `-r1` the second. A model has an entry only for the passes that finished. **The comparison is not complete for any model**:

- **Strata** (Qwen3.8-Flash-Next IQ3_S, MTP), **complete, two passes per arm (40 case-runs each), finished 2026-11-20 10:17:** `p3f` solved **12/40** against control **17/40** (Fisher p = 0.35). Passes: control 8 and 9, `p3f` 7 and 5. Paired by case and pass, control solved and `p3f` not in 10, the reverse in 5, both in 7, neither in 18 (exact sign test p = 0.30). Verdicts: control budget 19, solved 17, overfit 2, failed 2; `p3f` budget 21, solved 12, overfit 4, failed 3. Output tokens `p3f` / control 0.94 (per-case bootstrap 95 % 0.75-1.18), input tokens 0.97, same wall time. Pass-to-pass swing: 7 of 20 cases changed outcome between the two control passes and 2 of 20 between the two `p3f` passes. **Reading: no significant difference and no cost; the direction is unfavourable to `p3f`, as in the Mercury bench (145/152 against 148/152) and the deepseek bench (299/304 against 301/304).** Counting the discordant pairs of those three comparisons together (19 lost against 9 gained) gives a sign-test p of 0.087; that pooling was decided after seeing the data and mixes three different benchmarks, so it is a hypothesis, not a result. The public-repository pilot on Mercury is the planned test of it.
- **OxCoder 9B Q6_K**: only the second pass of each arm completed (3/20 control, 2/20 `p3f`, tokens +5 %); the first-pass runs have 19 of 20 cases and no summary (the last case could not run, a path missing in one repository snapshot; the runner was fixed afterwards, the first passes were never completed). On the 19 common cases of both passes: 4/38 control, 5/38 `p3f`.
- **Mellum2.1 12B-A2.5B Thinking Q6_K** (no MTP; its MTP load failed): first pass control 1/20 against `p3f` 4/20; it ran out of the tool budget on 19 of 20 cases in control. No second pass.

Reading: for the two small models the share of solved cases is so low (5-20 %) that control against `p3f` cannot be told apart from run-to-run noise (one pass per arm; on Strata only 3 cases are solved by both arms in the first pass, 9 differ in either direction). Work on OxCoder and Mellum was stopped by the owner after these passes because more passes would cost hours of GPU without being able to separate the arms. DaisyRose-27B Q4_K_M was also stopped by the owner before any pass completed (about 16 h projected per pass of 20 cases at ~29 tok/s, extrapolated from one finished case); nothing about it is counted. Load notes, speed and KV calibration are in `daisyrose-27b/`. No result exists for how the rule affects this model.

## Known quirks

- Two of the 40 Strata runs (one per arm) ended because the model wrote its next tool call as plain text instead of a parsed call (`<tool_call><function=read>...`), which the agent took as its final answer: counted as `failed`, one per arm.
- `budget` is the most frequent verdict on every model (Strata 10 of 20 in both arms). It means unfinished within 60 tool calls, not a wrong answer; where the budget runs out in both arms the closing line has no room to matter.
- The runner crashed at the end of the first OxCoder and Mellum passes because one case's file path did not exist in a repository snapshot; fixed (missing paths skipped, finished cases kept on rerun). The Strata passes ran with the fixed runner.
