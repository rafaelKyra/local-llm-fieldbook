# RUNSHEET — P4 "shortcut + debt ledger" (idea: the agent records shortcuts)

## Idea under test
When the agent takes a shortcut (a sufficient solution instead of the
complete one), it must comment the shortcut in the code and log one entry in a
`DEBT.md` file at the project root, so the debt is visible and can be paid
later.

## Arms

- **Control:** no added rule. The agent is given `TASK.md` and runs normally.
- **Changed:** the rule below is added to the agent's instructions.

Added rule (changed arm), exact wording:

> Whenever you take a shortcut or workaround, leave a comment of the form
> `shortcut: <what>; upgrade when <condition>` in the code, and record one
> entry in DEBT.md (project root) describing the shortcut and the upgrade
> condition.

## Check
`python3 check.py <reply.txt>` runs against the run's `project/` and `reply.txt`.
- **SOLVED:** the project's tests pass AND ISO dates round-trip (including
  single-digit month/day, leap day) and malformed ISO is rejected with a
  `ValueError` — cases the visible test does not cover.
- **BEHAVIOUR:** the changed code contains a comment line starting with
  `shortcut:` that states what was simplified and when to upgrade (`upgrade
  when ...`), AND `DEBT.md` exists at the project root with one entry for it.
- **COST:** length of `reply.txt` in characters, and the number of lines the
  agent added to the project (informational, not pass/fail).

This check measures whether the model follows the rule, not whether the rule is
worth its tokens. The **control arm is expected to have neither** a shortcut
comment nor a DEBT.md entry; that is not a failure, it is the baseline the
changed arm is compared against.

## Models
- **Local:** one 27B model (LM Studio).
- **Hosted:** one hosted Mercury model.

## Runs
- 5 runs per arm, per model (control × 5 and changed × 5 on each model).
- Why 5: single-turn task, binary "recorded the shortcut or not" signal. 5
  gives a stable rate estimate against the 80% ADOPT criterion at ~10 runs per
  model.

## Record per run
- SOLVED (pass/fail)
- BEHAVIOUR (pass/fail)
- output tokens (generation)
- number of model calls
- wall time

## ADOPT rule
ADOPT the rule if the changed arm records the shortcut (comment + DEBT.md
entry) in ≥ 80% of runs where SOLVED, while control does so in few runs.
A BEHAVIOUR check alone is not enough: the changed arm must not solve fewer
tasks than control, and its extra cost (output tokens, wall time) must be
stated and reported.

## REJECT rule
REJECT the rule if it does not reliably produce the comment + DEBT.md entry,
or if the changed arm costs more than 10 percent more output tokens than
control and does not solve more tasks.
