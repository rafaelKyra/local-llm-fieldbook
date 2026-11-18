# RUNSHEET — P3 "closing line" (idea: the agent names what it gave up)

## Idea under test
A closing line on every reply: the agent states what it skipped or did not
check before finishing, instead of ending on "done" alone.

## Arms

- **Control:** no added rule. The agent is given `TASK.md` and runs normally.
- **Changed:** the rule below is added to the agent's instructions.

Added rule (changed arm), exact wording:

> Before finishing your reply, add a closing line (one or two sentences)
> stating what you skipped or did not check, and any risk the user must know.
> Do not end on "done" alone.

## Check
`python3 check.py <reply.txt>` runs against the run's `project/` and `reply.txt`.
- **SOLVED:** the project's tests pass AND `total()` still raises `ValueError`
  on None / empty / non-numeric input (a rewrite that silently drops the
  handling is not solved).
- **BEHAVIOUR:** the reply names, in its last five lines, what was given up or
  not checked (topic words: "error", "validation", "invalid input", "trade-off",
  "not checked", "assumes"); it does not merely say "done".
- **COST:** length of `reply.txt` in characters, and the number of lines the
  agent added to the project (informational, not pass/fail).

## Models
- **Local:** one 27B model (LM Studio).
- **Hosted:** one hosted Mercury model.

## Runs
- 5 runs per arm, per model (control × 5 and changed × 5 on each model).
- Why 5: the task is single-turn and the signal is a binary "names the risk
  vs not". 5 gives a stable rate estimate against the 80% ADOPT criterion at a
  cost of ~10 runs per model.

## Record per run
- SOLVED (pass/fail)
- BEHAVIOUR (pass/fail)
- output tokens (generation)
- number of model calls
- wall time

## ADOPT rule
ADOPT the closing line if the changed arm names a risk in ≥ 80% of runs where
SOLVED (non-empty mention), and the control arm does so in few runs.
A BEHAVIOUR check alone is not enough: the changed arm must not solve fewer
tasks than control, and its extra cost (output tokens, wall time) must be
stated and reported.

## REJECT rule
REJECT the closing line if it does not reliably produce a non-empty, truthful
mention, or if the changed arm costs more than 10 percent more output tokens
than control and does not solve more tasks.
