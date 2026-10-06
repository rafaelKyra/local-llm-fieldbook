# Fieldbook

Dated field notes on running local LLMs for agentic coding. Measured, repeated, and corrected in public.

Two kinds of entry, kept apart on purpose:

- **Measurements.** Raw answers, a scorer, pinned load settings. Anyone can re-score them.
  Models are grouped in *bands*, never ranked by position.
- **Field notes** (`field-notes/`). Impressions from real work, dated and scoped. They are
  not scored, not ranked, and never mixed into a measurement table.

A field note can be right and still not be a measurement. Fieldbook keeps the two apart so a
reader always knows which one they are looking at.

**Read the report:** <https://rafaelkyra.github.io/local-llm-fieldbook/>
(generated from the data by `harness/build_report.py`; source in `docs/index.html`).

## Reproduce the current table (no GPU needed)

```bash
python3 harness/score_grid.py data/grid-2026-09-20/answers
python3 harness/task1_failure_modes.py data/grid-2026-09-20/answers
```

`data/grid-2026-09-20/` holds the saved answers of 17 model builds on a 14-task coding grid,
one run each, plus the published result files. Re-scoring reproduces the published per-task
pass counts exactly (e.g. task 1: 3/17, task 8: 9/17).

Rig: dual Xeon E5-2680 v4, 192 GB DDR4 ECC, one RTX 3090 24 GB, LM Studio.

## What the data shows so far

| # | Finding | Status |
|---|---|---|
| 1 | A 14-task, single-run grid **cannot rank** these models. 16 of 17 builds fall in one band; only one separates from the rest. | Reproducible here |
| 2 | **Truncation moves scores.** Four points rest on answers cut off at the 8,192-token cap and counted as passes by the visible text. Counted strictly, `qwen3.8-27b@q4_k_s` drops from 13/14 to 12/14. | Reproducible here |
| 3 | **Task 1 does not measure obedience to a tool contract.** The model is never told to use search → read → write: that sequence is only in the hidden pass criteria. Of 14 failing answers, 13 never emit `write_file` and 7 use `sed`. A one-line `grep … \| xargs sed -i` fulfils the request as written. | Reproducible here |
| 4 | Where models differ, they differ **by task**, not along one axis. | Matrix in `data/grid-2026-09-20/scores.json` |

How bands are formed: models are sorted by passes out of all tasks (an incomplete answer counts
against), a Wilson 95% interval is computed over the tasks, and a model joins the current
band while its interval overlaps its band leader's. Models in one band are not ranked against
each other. The interval reflects only which 14 tasks were chosen; run-to-run noise needs
repeated runs, which `harness/run_all.sh` supports (`RUNS=3`).

## Second ruler: live orchestration (2026-10-04)

A different ruler, kept apart from the grid above: one fixed, read-only verification task on a real project, run through
a real orchestration arm (**Harness Lab, primary arm**: plan, approval, step-by-step execution, recovery, evidence gate).
It measures **model + harness together**, on 31 models, not coding ability. The protocol was registered before the
confirmatory runs: [`harness/live-orchestration/PROTOCOL.md`](harness/live-orchestration/PROTOCOL.md). Data, sanitised,
in `data/live-orchestration-2026-10-04/` (`run1/`, `run2/`, `run3/`, `analysis.json`).

| # | Finding | Status |
|---|---|---|
| 1 | One run is not a measurement. 8 of 31 models passed in run 1; of the 14 models run three times, only **2 passed every run** (`holo4-35b-a3b-i1`, `cyber-tiel-coder-35b-a3b-apex-i-nanoplus`), 3 passed twice, and only 4 of 14 gave the same verdict in all three runs. | Measured here |
| 2 | Across the 42 runs of the repeated models: 17 passes, 14 partial reports, 6 ten-minute timeouts, 4 runs that wrote into the project, 1 empty report. | Measured here |
| 3 | The extremes separate, the middle does not: 3/3 against 0/3 gives Fisher exact two-sided p = 0.10; the Wilson intervals of the best and the worst overlap (0.44-1.00 against 0.00-0.56). | Measured here |
| 4 | Some models write files although the prompt says not to modify any file (4 models in run 1, 4 further runs among the repeated ones). | Measured here |
| 5 | One model family fails at once with an HTTP 400 grammar error from the runtime before any tool runs (one run, not repeated). | Single run, not claimed as reproducible |

Not reproducible end to end from this repository: the arm's code is not published. The prompt, load settings, runner
(`harness/live-orchestration/live-eval.sh`), analysis (`analyze.py`), sanitiser (`sanitize.py`) and every run's
sanitised result are. Findings about the arm itself are secondary and are in the report.

### Replication, new models, and correcting the arm (2026-10-04 and 2026-10-05)

Finding 1 above did not survive a replication made the same day: the two models that passed three times were run again
under three LM Studio configurations, three runs each, and neither repeated three passes in any cell (`replication/`).
Read finding 1 as "passed three times, once". Models added later are in `new-models/`, one to four runs each, with the
settings used stored in every result.

Running many models also exposed faults in the arm itself. They were corrected in steps and the same four models were run
again three times after each step (`arm-iterations/`, versions v2 to v10; v1 is the earlier data):

| # | Finding | Status |
|---|---|---|
| 6 | The first batch of corrections made the result worse: a safety default refused the build commands the task ordered (a stderr merge was read as a file redirect), and the dense base model went from 3 of 3 passes to 0 of 3. The rerun showed it; it was corrected. | Measured here |
| 7 | After the corrections of v4 no run wrote into the project and the read-only policy refused no command (v3 had six refusals of read-only commands). The pass count moved within noise (9, 8 and 8 of 12 in v3, v4 and v5): the corrections are judged by the failure they removed, not by a better score. | Measured here |
| 8 | v5 gave the report step the last lines of the latest commands, to stop reports from lacking a fact. It did not work as hoped: four of twelve reports still lack one fact in v4 and again in v5. Reported as it came out. | Measured here |
| 9 | v6 closes tool use for a step after five refused calls (a model had asked fourteen times to write into the read-only project). Judged against four criteria written beforehand: three met, one not exercised live (shown by a unit test); 7 of 12 passes against 8 in v5, within noise. | Measured here |
| 10 | v7 (replan, one definition of a write, early probes kept) met its four criteria. v8 (the lane that revises the draft is given the whole task) corrected a real fault but did not meet its criteria: 6 passes against a target of 8, and 6 reports with a fact missing against a target of at most 2. The missing test total is partly a model listing per-class counts without adding them, which the check does not accept: a stricter proxy than the task's wording. | Measured here |
| 11 | v9 (the corrections made after the outside review) did not meet two of its four criteria written beforehand: five passes against a target of seven, and the evidence gate refused in seven of twelve runs against a target of three. Nothing was written into the project. The corrections have not, as yet, shown an effect in a live run. | Measured here |
| 12 | v10 followed from a measurement: the gate was made to report why it refused, and it showed that a read-only shell command was not recognised as an inspection. After the correction the gate refused in 2 of 12 runs, against 7 in v8 and v9 (met); 6 passes against a target of 7 (not met). In five of the twelve runs the only missing fact is the test total: a report listing per-class counts without adding them up is scored as missing it, so most of what separates 6 passes from 10 is a property of the scorer, not of the arm. | Measured here |
| 13 | Still open and listed in the report: the final step still lacks some earlier output (the test count is missing from some reports), a second one-step replan is rejected, and the evidence gate can repeat a refusal until the time limit. | Open |

An independent review of the arm and of these corrections was made on 2026-10-06 (sources read, classification functions run, no live
model runs). Its verdict: the corrections fix real faults, but the read-only mode is a best-effort guard, not a guarantee that no
file changes, and must not be presented as a security boundary. It also found a miscount on this page (the evidence gate refused
in seven of twelve v8 runs, not nine; corrected). What it reproduced was corrected and what it did not was left open; the table
is in the report. The review is private because it describes ways around the guard. `harness/live-orchestration/arm_iterations.py`
now reproduces the per-version table from the data.

Twelve runs made while the runtime's server restarted under the batch were set aside as invalid and are in no table. Results
are labelled by arm version and must not be compared across versions as if the arm were the same.

## Reported earlier, not yet reproduced here

These come from an earlier hand-written report. The raw data is not in this repository, so
treat them as claims, not results:

- A 4,096-token cap turned a 13/14 model into 7/14 on the same text.
- Some GGUF chat templates reject a separate `system` parameter, so the Anthropic Messages
  API fails on them while the OpenAI-style API works.
- Without `--gpu max`, LM Studio can silently split a model between GPU and CPU.
- Executable repair of six real defects from a private repository: 0 valid fixes in 30 runs.
  The cases are private and are not published; only the method and results will be.

## What this does not claim

- One machine only. Speeds do not transfer.
- Single runs. No repeated-run data is published yet.
- Model files are community builds with unstable names. File hashes are not yet recorded, so
  an outsider cannot be sure they have the same weights.
- Pass rules are keyword and structure checks, not execution. A passing answer is not a
  verified solution.
- Outputs are generated by third-party models, each under its own license. Check them before
  reusing the answers.

See [CORRECTIONS.md](CORRECTIONS.md) for what has been retracted or changed, and why.

## Names and affiliation

Model names (Qwen, Gemma, Nemotron, MiniCPM, Phi and others) are trademarks of their owners and
are used only to say which model was tested. This project is not affiliated with, endorsed by or
sponsored by any of them. "Fieldbook" is used here as a plain description of a notebook of dated
field notes; it is not a product name, and this project is unrelated to any software of the same
name.

Results describe specific builds, run once on one machine; they are not statements about the
models' makers or about how the models behave elsewhere.

## Layout

```
harness/      runner, scorer, failure-mode classifier, the 14 task prompts
data/         saved answers and result files, one directory per measurement
field-notes/  dated impressions from real work (not measurements)
```

## License

- **Code** (`harness/`): Apache License 2.0, see [LICENSE](LICENSE).
- **Results, tables and text** (this README, `docs/`, `CORRECTIONS.md`, the result JSON files):
  Creative Commons Attribution 4.0, see [LICENSE-DATA](LICENSE-DATA).
- **Saved model answers** (`data/*/answers/`): these are outputs of third-party models, each
  under its own license. The author claims no rights over them and they are **not** covered
  by `LICENSE-DATA`. They are included only so the scoring can be reproduced.

Copyright 2026 Rafael Kyra.
