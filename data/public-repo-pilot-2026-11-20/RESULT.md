# Public-repository pilot on Mercury 3: control against `p3f` (20 cases from six public repositories, 2 passes per arm)

| arm | pass | solved | verdicts | output tokens | input tokens | tool calls | seconds |
|---|---|---|---|---|---|---|---|
| control | r0 | 17/20 | solved 17, budget 3 | 388482 | 16294942 | 860 | 4738 |
| control | r1 | 17/20 | solved 17, budget 3 | 429449 | 17196509 | 867 | 4003 |
| p3f | r0 | 18/20 | solved 18, budget 2 | 359699 | 14473025 | 815 | 3517 |
| p3f | r1 | 18/20 | solved 18, budget 2 | 380044 | 15307703 | 808 | 3807 |

**Solved:** `p3f` 36/40 against control 34/40 (Fisher p = 0.737). Paired by case and pass: both 33, neither 3, only `p3f` 3, only control 1 (sign test p = 0.625).
- control: 2 of 20 cases changed outcome between its two passes
- p3f: 2 of 20 cases changed outcome between its two passes

**Cost:** output tokens `p3f` / control 0.90 (per-case bootstrap 95 % 0.73-1.12); input tokens 0.89; tool calls 0.94; wall time 0.84.

## Cases that are not solved by both arms in both passes

| case | control r0, r1 | p3f r0, r1 |
|---|---|---|
| acp-v2-idle-on-local-command-echo | budget, solved | solved, budget |
| htmlparser2-end-handled-once | solved, budget | solved, solved |
| minisearch-browser-model-loaded-once | budget, budget | budget, solved |
| rulesync-bob-global-modes-merge | budget, budget | budget, budget |
