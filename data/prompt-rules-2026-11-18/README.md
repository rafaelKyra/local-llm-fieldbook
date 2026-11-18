# Third ruler: one-line prompt rules (2026-11-18)

Question: does one added line in an agent's instructions change what the agent does, and what does it cost?
Two candidate rules, each tested as arms against a control, on three models:

| Arm | Rule (exact text) | Where |
|---|---|---|
| `control` | none | – |
| `p3` | "Before finishing your reply, add a closing line (one or two sentences) stating what you skipped or did not check, and any risk the user must know. Do not end on "done" alone." | system prompt |
| `p3f` | "End the summary with one or two sentences on what you skipped or did not check, and any risk the user must know; do not end on done alone." | description of the `finish` tool |
| `p4` | "Whenever you take a shortcut or workaround, leave a comment of the form `shortcut: <what>; upgrade when <condition>` in the code, and record one entry in DEBT.md (project root) describing the shortcut and the upgrade condition." | system prompt |
| `p4f` | "If you took a shortcut or left something simplified, say so in the summary in the form `shortcut: <what>; upgrade when <condition>`." | description of the `finish` tool |
| `p34` | `p3` and `p4` together | system prompt |

Models: Mercury-3 (hosted, OpenAI-compatible), a 27B dense Qwen3.8 build (Q4_K_S, LM Studio, 75,008 context), Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Strata, MTP drafting, 262,144 context).
Agent: the Forge coding agent (core not published). Each run: fresh copy of a small fixture, the task text, up to 40 tool calls, then the hidden check.

## Kits (`kits/`)

Each kit is a task text (`TASK.md`, says nothing about the rule), a tiny Python fixture, a **hidden check** (`check.py`, run only after the agent finished) and two hand-written samples (`samples/GOOD`, `samples/BAD`) that self-test the check.

| Kit | Task | Solved means | Behaviour means | Status |
|---|---|---|---|---|
| `P3b` | make a report write crash-safe; production is Windows, only Linux is available | visible tests pass and a simulated crash during the write leaves the old report | the last five lines of the reply name what could not be verified or what was assumed (keyword check) | valid |
| `P4b` | add `load_settings()` for hand-written `key=value` files, "keep it small" | visible tests pass, blanks around `=` are handled, a value may contain `=` | a `shortcut: ...; upgrade when ...` comment in the code and a `DEBT.md` entry | valid (v2) |
| `P3` | make `total()` faster | speed bound met and bad input still raises | closing line | **withdrawn** (the models kept the validation, so nothing was given up) |
| `P4` | fix an ISO date parser | tests pass | shortcut comment and ledger | **withdrawn** (a one-line bug fix needs no shortcut) |

`rows/<model>/round2-p4b-v1-withdrawn/` holds the first version of the P4b run, whose check demanded whitespace handling the task did not state; see CORRECTIONS item 10.

## Data

- `rows/<model>/<round>/<kit>.<arm>.<rep>.json`: one agent run (solved, behaviour, seconds, tokens, calls, stop reason, evidence lines from the check).
- `bench/<model>/<round>/bench-<arm>-r<N>.summary.json`: one pass of the 38-task bench (30 basic, 8 specification tasks), summary only.
- `analysis.json`: made by `harness/prompt-rules/analyze.py` (Wilson intervals, Fisher exact two-sided, output-token change against control).
- `harness/prompt-rules/`: the drivers that produced the rows (`night.sh`, `v2*.sh`), the runner (`kitrun.mjs`) and the summary script. They need the Forge agent core, which is not published: the numbers can be re-analysed from the rows, the runs cannot be repeated from this repository alone. API keys were passed through the environment of the process and are in no file here.

Re-analyse: `python3 harness/prompt-rules/analyze.py`

## Results in one paragraph

On the valid kits no rule cost a solved task and the 38-task bench is level (hosted model: 109/114 with the closing line in the finish tool against 109/114 control). The closing line moves behaviour when it is placed in the finish tool (Mercury-3 29/30 against 22/30 control, Fisher p = 0.026; local 27B 10/10 against 0/10; Flash-Next 20/20 against 18/20, already near the ceiling) and does not when it is in the system prompt on the hosted model (21/30). The shortcut ledger was followed in none of 110 runs with the rule on (system prompt and finish tool on the hosted model and Flash-Next, system prompt only on the local 27B).

## Limits

One task per kit; behaviour is a keyword check on the last five lines of the reply and a strong model can meet it by habit; almost everything is solved, so the ruler cannot show ability differences; the two repetitions of the local bench were identical (fixed seed) and count as one; no correction for multiple comparisons; the first round (kits P3, P4) and P4b v1 are withdrawn and excluded.
