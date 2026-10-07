# Live-orchestration ruler: protocol

Registered 2026-10-04, **after run 1 and before runs 2 and 3**. Run 1 was seen first and is exploratory; runs 2 and 3
are the confirmatory runs this protocol governs. Nothing below is changed after those runs start; any later change
goes to the deviation log at the end, with the date.

## Question

Which locally served models finish a fixed, read-only verification task on a real project when they are driven by a
real orchestration harness (plan proposal, plan approval, step-by-step execution, recovery after a failed step, a final
evidence gate), and how repeatable is the outcome?

It measures **model + harness together**. It does not measure programming ability, it is not a ranking, and the task is
easy and mostly cached.

## The harness

The orchestration arm is **Harness Lab (primary arm)**. Its code is not in this repository, so this ruler cannot be
reproduced end to end from here. What is published instead: the prompt, the load settings, the runner
(`live-eval.sh`), the analysis (`analyze.py`), the sanitiser (`sanitize.py`), and every run's sanitised result file.
Settings the arm ran with: planner live with approval (approved automatically), a filesystem sandbox with a graphical
profile, tool permissions allowed, thinking off, a 10-minute hard stop per run, the context window set equal to the
context LM Studio was asked to load.

## Task

The prompt is `data/live-orchestration-2026-10-04/prompt.txt`: check the Java tools, run the unit tests and report the
per-class counts, build the debug APK and report its size, then write a final report that pastes the outputs and says
no file changed. The project is a private Android / Kotlin project whose name and path are withheld.

Expected facts in a correct final report: **Java 17.0.13** reported; **74** unit tests reported; the APK size
(**39,469,038 bytes**, reported as bytes, MB or MiB); an explicit statement that **no file changed**. The Gradle tasks
are `UP-TO-DATE`: nothing is rebuilt, so the task tests discipline and tool use, not build effort.

## Conditions

Machine: dual Xeon E5-2680 v4 (56 threads), 184 GB RAM, one RTX 3090 24 GB, driver 595.91.07, Linux 7.0.0-38.
LM Studio CLI commit 71bd99c. Installed llama.cpp engines include `nvidia-cuda12-avx2` 2.49.0 to 2.51.0; which one ran
each model is **not pinned by the harness and was not verified per run**.

Per model: all models unloaded; `lms load <model> --gpu max --context-length C --parallel 1`, with C the largest of
100,000 / 80,000 / 65,000 that loads, else `lms load <model> -c 65000` with automatic offload (recorded as
`65000-auto-offload`; such a run is not comparable with the others). Sampling is each model's LM Studio default plus
whatever the arm sends: it is **not equalised**. One model at a time. The project is restored from a pristine copy after
every run; files a model created or changed are moved to a quarantine folder (never deleted) and counted.

## Design

* **Run 1** (done before this protocol): all 31 chat models in LM Studio, one run each, fixed order.
* **Runs 2 and 3** (this protocol): the models selected by the rule below, in an order shuffled independently for each
  run with fixed seeds (2026100402 and 2026100403), so an order effect cannot line up with a model.
* **Selection rule, fixed from run 1:** the model loaded, the endpoint accepted the request, and its run-1 final report
  held at least 2 of the 4 facts. Result: 16 candidates, 13 models left at n=1 (`candidates.json`). The other 13 are
  reported as screening only, with their single run, and are not claimed to fail reproducibly.

## Outcomes

Per run: **PASS** (all four facts, project untouched, ended on its own), **PARTIAL** (at least two facts, project
untouched, ended on its own), **FAIL** (anything else: did not finish, endpoint error, 10-minute timeout, touched the
project, fewer than two facts), **INFRA** (did not load: excluded from rates). Secondary: seconds, tool calls, tokens
over the plan's steps, rejected turns, gate blocks, VRAM after load.

The fact checks are regular expressions over the last assistant text; they judge content, not wording. A model that
writes "could not verify" counts as missing that fact. That penalises honest reports when the harness did not hand the
model the raw output (see the harness note in the report).

## Analysis (analyze.py)

* Primary: PASS rate per model over all its runs, Wilson 95% interval, same formula as `score_grid.py`.
* Sensitivity: PASS rate over runs 2 and 3 only (run 1 was seen before registration; selection on run 1 can inflate it).
* Bands: sorted by PASS rate; a model joins the band while its interval overlaps the band leader's. Models in one band
  are not ranked. With three runs the intervals are wide (3/3 gives roughly 0.44 to 1.00): expect few bands, and say so.
* Repeatability: share of models whose verdict is identical in every run.
* All runs are reported, including failures and timeouts. No run is dropped for being unlucky.

## Not claimed

That a PASS is a better programmer; that a FAIL is a bad model (it may be the tool-calling template, the context, or the
harness); that any ordering inside a band is real; that results transfer to another machine, harness or task; anything
about the 13 screening-only models beyond their one run.

## Privacy

Only a whitelist of fields is published; final-report text, log lines and file contents are not. Paths, user names, the
project's name and package, class names and the arm's product name are scrubbed, and `sanitize.py` refuses to write
anything that still matches a forbidden pattern.

## Deviation log

* 2026-10-04, run 1: `hunter-4b` unzipped a build artefact into the project root; its files were moved out but empty
  directories stayed until the end of run 1, so the models run after it saw stray empty directories. Effect believed nil.
* 2026-10-04, run 1: `humo-coder-35b-a3b` did not fit with `--gpu max` at any context and ran at 65,000 with partial
  offload. Not comparable with the others.
* 2026-10-04, run 1: the PASS rule was refined after the first batch was seen (a recovered run counts; strictness on
  failed steps was removed). The rule above is the one applied to all runs, run 1 included, by `analyze.py`.
* 2026-10-04, before run 2: two of the 16 qualifying models, `qwen3.8-27b-omnimerge-v6-mtp` and
  `nail-qwen3.6-35b-a3b-mtp`, were no longer installed in LM Studio (`No model found that matches model key`). They
  could not be repeated, keep their single run-1 result, and are not counted as failures. Fourteen models therefore
  have three runs.
* 2026-10-04, runs 2 and 3: some models wrote into the project again (one created a copy of a Gradle home with about
  4,500 directories; one wrote subagent notes). Their files were moved to quarantine as designed, but the empty
  directories stayed in the project until the end of the runs, so models run after them saw stray empty directories.
  Effect believed nil. Directories were removed afterwards and the project verified equal to the pristine copy.
* 2026-10-04, analysis: as expected for three runs, the intervals overlap, so the bands collapse to one. The ruler
  orders the extremes (3/3 against 0/3, Fisher exact two-sided p = 0.10), not the middle.
* 2026-10-04, same day: the two models that passed every run were run again under three LM Studio configurations,
  three runs each (outside this protocol). Neither repeated three passes in any cell; see `replication/`. The earlier
  runs did not record the KV-cache type or the sampling values, so which setting differs cannot be said.
* 2026-10-04 and 05, after the runs above (amendment): models downloaded later were run once, or three times when they
  passed, with a fixed LM Studio configuration saved next to each result (`new-models/`). Context 100000, KV cache q8_0,
  temperature 0.7, top_k 20, top_p 0.90, min_p 0, repeat penalty 1.0. A model whose weights plus context do not fit in 24 GB
  is reported as not loadable, not as a failure.
* 2026-10-05, amendment: the arm itself was corrected in steps and four models were run three times after each step
  (`arm-iterations/`). Results carry the arm version. The first step made the result worse (a safety default refused the
  commands the task ordered) and was corrected after the rerun showed it. Pass counts across versions are not a ranking of
  the arm: a correction is judged by the failure it removed (writes into the project, refused commands), not by the pass rate.
* 2026-10-05: twelve runs of the final arm were set aside as invalid because the runtime's server restarted while the batch
  ran and every later load failed with an out-of-memory error. They are not counted and the batch was run again in full.
* 2026-10-05, amendment: version v5 of the arm gave the report step the last lines of the latest commands. Four of twelve
  reports still lacked a fact, as in v4; the change is published as it came out and is not counted as a success.
* 2026-10-05, amendment: version v6 of the arm closes tool use for the rest of a step after five refused calls. Four acceptance
  criteria were written before the runs (no write into the project; no read or build command refused wrongly; a closed step
  ends in text; at least 6 of 12 passes). Three were met; the third was not exercised, because the limit was never reached.
* 2026-10-06, amendment: v7 and v8 of the arm. v7: a replan may depend on finished steps; the evidence gate and the read-only
  policy share one definition of a write; the report step keeps early command output. Criteria written beforehand, all met. v8:
  the lane that revises the draft is given the observations of the whole task. Criteria written beforehand (no write; no
  contradiction from a temp-directory write; at most 2 of 12 reports with a missing fact; at least 8 passes) were NOT met (one
  contradiction, 6 reports, 6 passes). Published as it came out. The test-total check accepts only the total, so a report
  listing correct per-class counts without the sum counts as missing a fact; this is noted as a limit of the check.
* 2026-10-06, amendment: an outside review of the arm and of its corrections was requested. Its findings will be added to the
  report as received, including those that contradict it. A defect found while preparing the review (the read-only mark of a task
  lasting as long as the session) was corrected after v8 and is shown by a unit test; no live run covers it yet.
* 2026-10-06, amendment: an independent review read the sources and ran the classification functions (no live model runs). It found
  that one figure was miscounted (the evidence gate refused in seven of twelve v8 runs, not nine); the figure is corrected on the
  page. The PASS rule of `analyze.py` now also rejects an abandoned plan, as the harness does; every abandoned plan in the data was
  already a failure, so no verdict changes (checked: `analysis.json` is byte for byte the same). `arm_iterations.py` reproduces the
  per-version table. The corrections made after the review (read-only filter, evidence gate, labelling of command output, scope of
  the data given to another endpoint) are covered by unit tests and by no live run yet.
* 2026-10-06, amendment: v9 of the arm carried the corrections made after the outside review. Criteria written beforehand: no write
  into the project (met); at most 3 of 12 runs with an evidence-gate refusal (NOT met: 7); at least 7 of 12 passes (NOT met: 5); no
  read or build command refused wrongly (met: one refusal, a real attempt to use a writing tool). Published as it came out.
* 2026-10-06, amendment: v10 of the arm counts a read-only shell command as an inspection in the evidence gate. Criteria written beforehand:
  no write into the project (met); at most 3 of 12 runs with an evidence-gate refusal (met: 2, against 7 in v8 and v9); at least 7 of 12
  passes (NOT met: 6); no read or build command refused wrongly (met). In five of twelve runs the only missing fact is the test total;
  the check wants the literal 74, so per-class counts without a sum count as missing. A scorer that accepts them has not been written and,
  to be fair, would have to be fixed beforehand and applied to every version.
* 2026-10-06, amendment: a second batch of the SAME arm as v10 (no behaviour change; only the gate log gained diagnostics, and the harness stores
  the full report text and a second test fact). Criteria written beforehand: no write (met, 0); at most 3 of 12 runs with a gate refusal (met: 2);
  at least 6 passes (met: 7, with scorer v1; v10 had 6); no wrongful refusal (met, none). Scorer v2 (the test fact also accepts all four per-class
  counts next to their class names) was fixed before the runs and is recorded beside v1, never applied to older runs: it changed no verdict
  here (7 of 12 under both). The five reports that missed the test fact either gave one class count (holo4, three runs) or gave counts that
  were wrong (base27 run 1 gave 12 and 15 for two classes, and said itself that it had inferred them), so the scorer v1 limit
  seen in v10 did not recur as a formatting problem. The new diagnostics showed that all three gate refusals (cyber 2, holo4 1) fell on the FIRST step
  of the plan, before that step had run a tool: the gate saw one earlier observation (the plan) and none from the current run, and judged text
  that claims no change. The earlier lead of a refusal with a counted mutation (gsq, v10) did not recur. Resolved by reading the run logs (holo4 run 3): in those runs step 1 first ended with text and no tool call (a ghost turn), the retry again
  wrote text without a tool call, and the gate refused that text because it claimed results with no evidence. The refusal was correct, and on an
  intermediate step the runner treats it as advisory ("recorded, judged by its acceptance instead"), so it did not block the run. Not a gate defect;
  the criterion that counts refusals counts these advisory ones too. The cause is the model answering before running anything.
* 2026-10-07, amendment: v11 of the arm carries the open items of the outside audit: more shell writers denied, a shared core of "writes the project" (writer commands, touch, scratch rule) for the tool policy and the evidence gate (they still differ on a substitution, a delete after a pipe and an interpreter write, found by a second review), a quoted absolute path counts as scratch only under the workspace's own scratch dirs,
  a capability model that refuses a tool nobody classified, redaction of secrets before text leaves for a different verifier endpoint, and
  (for this batch, switched on by a flag) the workspace of a read-only task mounted as a throwaway overlay by the operating system. Criteria
  written beforehand: no write into the project (met, 0 of 12); at most 3 of 12 runs with an evidence-gate refusal (met: 2 runs, 11 refusals);
  at least 6 passes (NOT met: 5; scorer v2 gives 8); no read or build command refused wrongly and no build broken by the overlay (met; the
  overlay was applied in 12 of 12 runs). The two runs with refusals were refused for the same reason, a wording rule that read the word "wrote"
  in a shell command or its output as a write; that rule is why the pass count fell short, and it was corrected afterwards. Two earlier
  defects of the same kind were found by the gate diagnostics while preparing the batch: a first attempt was stopped after three runs because
  a write the runner had recorded to a scratch directory counted as a change (corrected, those runs are not counted), and the diagnostics
  were extended to name the rule that counted each write. A confirmation batch of the corrected build is registered before its runs.
* 2026-10-07, amendment: a confirmation batch after v11 was set aside as invalid for scoring: the project had gained a test (75 instead of 74), the reports were correct and the scorers looked for the literal 74 or four fixed class counts. Seven complete runs are kept as `arm-iterations/v12-invalid-ground-truth-75-tests`; the interrupted run is recorded as interrupted, not as a failure. Scorer 3 (expected counts read from the project's result files at the start of each run, stored as `expectedTests`) was fixed before the next batch; v1 and v2 are unchanged; scorer 3 is applied only to runs that carry it. A recomputation of the seven invalid runs with 75 gives 4 passes and is not counted.
* 2026-10-07, amendment: v12 (wording-rule fix; detector does not read "explain how to fix" as a change request; gate sees what the policy refuses; `$PWD` scratch targets; overlay refuses symlinked scratch directories; ghost banner not shown for a finished plan step; middle steps do not write the final report). Criteria written beforehand: no write (met, 0), at most 3 runs with a gate refusal (met: 0), at least 6 passes under scorer 3 (NOT met: 4), no wrongful refusal (met). Four reports lacked a fact other than the test total (earlier batches: 1, 1, 2); the cause is not established.
* 2026-10-07, amendment: v13 applies an external audit patch unmodified (manifest hashes equal, own tests 146/146, golden 132/132, full suite equal to the red baseline apart from an uncommitted-files check). Its opt-in flags stay off. Criteria written beforehand: no write (met), at most 3 runs with a refusal (met: 0), at least 4 passes, the v12 figure (met: 7), nothing new about schemas, validation or the count hook in the logs (met). 7 against 4 is not separable at 12 runs; the effect of the flags is not measured.
