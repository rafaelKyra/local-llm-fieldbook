"""The live-orchestration ruler as an HTML section for the public report.

Every number comes from data/live-orchestration-2026-10-04/analysis.json (written by live-orchestration/analyze.py),
so re-analysing and rebuilding cannot drift apart. Only the framing text is typed.
"""
import glob, html, json, os
from math import comb
from pathlib import Path

e = html.escape
SYM = {"PASS": "P", "PARTIAL": "~", "FAIL": "x", "INFRA": "–"}


def build(data_dir: Path) -> str:
    path = data_dir / "analysis.json"
    if not path.exists():
        return ""
    rows = json.loads(path.read_text(encoding="utf-8"))
    cands = json.loads((data_dir / "candidates.json").read_text(encoding="utf-8"))
    repeated = [r for r in rows if r["runs"] >= 2]
    once = [r for r in rows if r["runs"] < 2 and r["verdicts"] and r["verdicts"][0] != "INFRA"]
    infra = [r for r in rows if r["runs"] == 0]

    def fmt(x, nd=0):
        return "–" if x is None else (f"{x:.{nd}f}" if nd else f"{x:.0f}")

    def line(r, with_band):
        verdicts = " ".join(SYM[v] for v in r["verdicts"])
        ci = f'{r["pass"]}/{r["runs"]} · {r["ci95"][0]:.2f}–{r["ci95"][1]:.2f}'
        rep = {True: "yes", False: "no", None: "n=1"}[r["repeatable"]]
        band = f'<td class="n">{r["band"]}</td>' if with_band else ""
        ctx = r.get("loadedContext") or "–"
        vram = f'{(r["vramMiB"] or 0) / 1024:.1f}' if r.get("vramMiB") else "–"
        return (f'<tr>{band}<td class="mono">{e(r["model"][:46])}</td><td class="n">{r["runs"]}</td>'
                f'<td class="mono">{verdicts}</td><td class="n">{ci}</td><td class="n">{fmt(r["median_seconds_when_finished"])}</td>'
                f'<td class="n">{fmt(r["median_tokens_when_finished"])}</td><td class="n">{vram}</td>'
                f'<td class="n mut">{e(str(ctx))}</td><td class="n">{rep}</td></tr>')

    head = ('<th>Model</th><th>Runs</th><th>Verdicts</th><th>PASS · 95% interval</th><th>Median s</th>'
            '<th>Median tokens</th><th>VRAM GB</th><th>Context</th><th>Repeats</th>')
    rep_rows = "".join(line(r, True) for r in repeated)
    once_rows = "".join(line(r, False) for r in once)
    inf = ", ".join(e(r["model"]) for r in infra) or "none"
    unavailable = [m for m in cands["candidates"] if any(r["model"] == m and r["runs"] < 2 for r in rows)]
    causes = {}
    for run_dir in sorted(glob.glob(str(data_dir / "run*"))):
        for f in glob.glob(os.path.join(run_dir, "*.json")):
            d = json.load(open(f))
            if d.get("model") not in {r["model"] for r in repeated} or d.get("loadFailed"):
                continue
            facts = sum(1 for v in (d.get("reportChecks") or {}).values() if v)
            if d.get("upstreamError"):
                c = "endpoint error"
            elif d.get("timedOut"):
                c = "10-minute timeout"
            elif not d.get("readOnlyKept", True):
                c = "wrote into the project"
            elif facts == 4:
                c = "pass"
            elif facts >= 2:
                c = "partial (2 or 3 facts)"
            else:
                c = "report holds fewer than 2 facts"
            causes[c] = causes.get(c, 0) + 1
    cause_text = ", ".join(f"{k}: {v}" for k, v in sorted(causes.items(), key=lambda x: -x[1]))
    full = [r for r in repeated if r["runs"] == 3]
    best, worst = (max(r["pass"] for r in full), min(r["pass"] for r in full)) if full else (0, 0)
    fisher = ""
    if full and best == 3 and worst == 0:
        fisher = (f"<p>Even the best against the worst separate only weakly: 3 of 3 against 0 of 3 gives a Fisher exact "
                  f"two-sided p = {2 / comb(6, 3):.2f}. Three runs per model can order the extremes, not the middle.</p>")
    add_rows = ""
    for f in sorted(glob.glob(str(data_dir / "addendum" / "*.json"))):
        d = json.load(open(f))
        facts = sum(1 for v in (d.get("reportChecks") or {}).values() if v)
        wrote = not d.get("readOnlyKept", True)
        v = ("FAIL" if (d.get("timedOut") or d.get("upstreamError") or d.get("stepsFailed") or d.get("aborts") or wrote)
             else "PASS" if facts == 4 else "PARTIAL" if facts >= 2 else "FAIL")
        note = "wrote into the project" if wrote else ""
        add_rows += (f'<tr><td class="mono">{e(d["model"][:46])}</td><td class="mono">{SYM[v]}</td>'
                     f'<td class="n">{fmt(d.get("elapsedSeconds"))}</td><td class="n">{fmt(d.get("stepTokens"))}</td>'
                     f'<td class="n">{d.get("toolCalls", "–")}</td><td class="n">{d.get("loadedContext") or "–"}</td>'
                     f'<td class="mut">{note}</td></tr>')
    addendum = (f'''<p><b>Addendum: the two missing models, one extra run each.</b> Both were reinstalled after runs 2 and 3
and run once, same prompt and settings, outside the registered protocol. They do not change the table above.</p>
<div class="sc"><table><thead><tr><th>Model</th><th>Verdict</th><th>Seconds</th><th>Tokens</th><th>Tool calls</th><th>Context</th><th>Note</th></tr></thead>
<tbody>{add_rows}</tbody></table></div>''' if add_rows else "")
    repl = ""
    rdir = data_dir / "replication"
    if rdir.exists():
        labels = [
            ("newcfg", "KV cache q8_0; sampling from the model cards (temperature 0.6, top_p 0.95, top_k 20, repeat 1.0; min_p 0 for holo4, 0.05 for cyber-tiel)"),
            ("cellA", "KV cache q4_0; sampling from the model card (temperature 0.6, top_p 0.95, top_k 20, min_p 0, repeat 1.0)"),
            ("cellB", "KV cache q8_0; sampling as the owner normally sets it (temperature 0.7, top_p 0.90, top_k 20, min_p 0, repeat 1.0)"),
        ]

        def v_of(d):
            facts = sum(1 for x in (d.get("reportChecks") or {}).values() if x)
            if d.get("upstreamError") or d.get("timedOut") or d.get("threw") or d.get("noResult") or not d.get("readOnlyKept", False):
                return "FAIL"
            return "PASS" if facts == 4 else "PARTIAL" if facts >= 2 else "FAIL"

        trs = ""
        new_pass = new_n = 0
        for key, label in labels:
            for model in ("holo4-35b-a3b-i1", "cyber-tiel-coder-35b-a3b-apex-i-nanoplus"):
                ds = [json.load(open(f)) for f in sorted(glob.glob(str(rdir / f"{key}-run*" / f"{model}.json")))]
                if not ds:
                    continue
                vs = [v_of(d) for d in ds]
                secs = sorted(d["elapsedSeconds"] for d in ds if d.get("elapsedSeconds") is not None)
                if model.startswith("holo4"):
                    new_pass += sum(v == "PASS" for v in vs)
                    new_n += len(vs)
                trs += (f'<tr><td>{e(label)}</td><td class="mono">{e(model[:24])}</td><td class="mono">{" ".join(SYM[v] for v in vs)}</td>'
                        f'<td class="n">{fmt(secs[len(secs) // 2]) if secs else "–"}</td></tr>')
        old = next((r for r in rows if r["model"].startswith("holo4")), None)
        fisher2 = ""
        if old and old["runs"] == 3 and old["pass"] == 3 and new_n:
            tot, succ = 3 + new_n, 3 + new_pass
            p_two = sum(comb(succ, k) * comb(tot - succ, 3 - k) for k in range(0, 4)
                        if comb(succ, k) * comb(tot - succ, 3 - k) <= comb(succ, 3) * comb(tot - succ, 0)) / comb(tot, 3)
            fisher2 = (f"For holo4, the original 3 of 3 against {new_pass} of {new_n} in the replication gives a Fisher exact "
                       f"two-sided p = {p_two:.3f}.")
        repl = f"""<h3>Replication check, same day (outside the registered protocol)</h3>
<div class="note"><b>The 3-of-3 result did not repeat.</b> After the confirmatory runs, the two models with a stable verdict were
run again under three different LM Studio configurations, three runs each. Neither model reproduced three passes in any
cell. The original runs did not record the KV-cache type or the sampling values (the harness sends none, so the runtime
applies its own), so the replication cannot say which setting differs; the runtime's engine selection did not change between
the later original runs and the replication (judged from its preference file, not from a per-load log). {fisher2} Read the stable verdict above as "passed three times, once", not as a
property of the model.</div>
<div class="sc"><table><thead><tr><th>Configuration</th><th>Model</th><th>Verdicts</th><th>Median s</th></tr></thead><tbody>{trs}</tbody></table></div>
"""
    newm = ""
    ndir = data_dir / "new-models"
    if ndir.exists():
        reasons = {
            "qwen3.8-27b-iu4-kairic-edge": "not loadable: the installed engine rejects its tensor type",
            "qwen3.8-27b-turbo-fable-cold-fusion-735-882-heretic-uncensored-neo-coder-max-mtp": "does not fit in 24 GB VRAM",
            "hcompany.holotron4-30b-a3b": "does not fit in 24 GB VRAM",
        }

        def vn(d):
            if d.get("loadFailed"):
                return "INFRA"
            facts = sum(1 for x in (d.get("reportChecks") or {}).values() if x)
            if d.get("upstreamError") or d.get("timedOut") or d.get("threw") or d.get("noResult") or not d.get("readOnlyKept", False):
                return "FAIL"
            return "PASS" if facts == 4 else "PARTIAL" if facts >= 2 else "FAIL"

        groups = {}
        for f in sorted(glob.glob(str(ndir / "*" / "*.json"))):
            d = json.load(open(f))
            if "model" not in d:
                continue
            name = d["model"].split("/")[-1].replace(".gguf", "")
            groups.setdefault(name, []).append((os.path.basename(os.path.dirname(f)), d))
        trs = ""
        order = {"PASS": 0, "PARTIAL": 1, "FAIL": 2, "INFRA": 3}
        rows_new = []
        for name, items in groups.items():
            vs = [vn(d) for _, d in items]
            secs = sorted(d["elapsedSeconds"] for _, d in items if d.get("elapsedSeconds") is not None)
            vram = max((d.get("vramMiBAfterLoad") or 0) for _, d in items)
            limit = "20 min (3 runs) and 10 min (1 run)" if any(k.startswith("dense20") for k, _ in items) else "10 min"
            note = reasons.get(name, "")
            rows_new.append((min(order[v] for v in vs), name, vs, secs, vram, limit, note))
        for _, name, vs, secs, vram, limit, note in sorted(rows_new):
            trs += (f'<tr><td class="mono">{e(name[:46])}</td><td class="n">{len(vs)}</td>'
                    f'<td class="mono">{" ".join(SYM[v] for v in vs)}</td><td class="n">{fmt(secs[len(secs) // 2]) if secs else "–"}</td>'
                    f'<td class="n">{vram / 1024:.1f}</td><td class="n mut">{e(limit)}</td><td class="mut">{e(note)}</td></tr>')
        newm = f"""<h3>Models added after the confirmatory runs (same day, outside the registered protocol)</h3>
<p>Each was downloaded later and run with a fixed LM Studio configuration saved next to the result: context 100000, KV cache q8_0,
temperature 0.7, top_k 20, top_p 0.90, min_p 0, repeat penalty 1.0. Only one model, Qwen3.8 27B GSQ RCO (IQ3_S), got
repeats: it passed in two of three confirmatory runs and in its first screening run. The dense Holo4 27B was run once at the
registered 10-minute limit and three times at 20 minutes; the extra time did not change the outcome. Published benchmark
scores for that model are for computer-use tasks, which this verification task is not. One run per model is an observation,
not a ranking.</p>
<div class="sc"><table><thead><tr><th>Model</th><th>Runs</th><th>Verdicts</th><th>Median s</th><th>VRAM GB</th><th>Limit</th><th>Note</th></tr></thead><tbody>{trs}</tbody></table></div>
"""
    arm = ""
    adir = data_dir / "arm-iterations"
    if adir.exists():
        models_arm = [("base27", "qwen3.8-27b"), ("gsq", "qwen3.8-27b-gsq-rco"),
                      ("cyber", "cyber-tiel-coder-35b-a3b-apex-i-nanoplus"), ("holo4", "holo4-35b-a3b-i1")]
        v1_src = {"base27": "new-models/base27-run*", "gsq": "new-models/gsq-run*", "holo4": "replication/cellB-run*"}
        v_dirs = {"v2": "v2-first-fixes-with-regression", "v3": "v3-corrected", "v4": "v4-final", "v5": "v5-latest-outputs", "v6": "v6-closing-after-refusals", "v7": "v7-replan-gate-facts", "v8": "v8-verifier-whole-task", "v9": "v9-audit-corrections", "v10": "v10-shell-inspection"}

        def va(d):
            facts = sum(1 for x in (d.get("reportChecks") or {}).values() if x)
            if d.get("upstreamError") or d.get("timedOut") or d.get("threw") or d.get("noResult") or not d.get("readOnlyKept", False):
                return "FAIL"
            return "PASS" if facts == 4 else "PARTIAL" if facts >= 2 else "FAIL"

        def load_runs(version, tag, model):
            if version == "v1":
                pat = v1_src.get(tag)
                files = sorted(glob.glob(str(data_dir / pat / f"{model}.json"))) if pat else []
            else:
                files = sorted(glob.glob(str(adir / v_dirs[version] / f"{tag}-run*" / f"{model}.json")))
            return [json.load(open(f)) for f in files]

        table = {}
        for tag, model in models_arm:
            table[tag] = {v: load_runs(v, tag, model) for v in ("v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10")}
        vt = ""
        for tag, model in models_arm:
            cells = ""
            for v in ("v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10"):
                runs = table[tag][v]
                cells += (f'<td class="mono">{" ".join(SYM[va(d)] for d in runs) if runs else "n/a"}</td>')
            vt += f'<tr><td class="mono">{e(model[:40])}</td>{cells}</tr>'
        mech = ""
        for v, label in (("v1", "v1 · as first run"), ("v2", "v2 · first corrections (with a regression)"),
                         ("v3", "v3 · regression corrected"), ("v4", "v4 · quoting and scratch paths corrected"),
                         ("v5", "v5 · report step given the latest command output"),
                         ("v6", "v6 · tool use closed after repeated refusals"),
                         ("v7", "v7 · replan, one definition of a write, early probes kept"),
                         ("v8", "v8 · verification lane given the whole task"),
                         ("v9", "v9 · corrections after the outside review"),
                         ("v10", "v10 · a read-only shell command counts as inspection")):
            runs = [d for tag, _ in models_arm for d in table[tag][v]]
            if not runs:
                continue
            passes = sum(va(d) == "PASS" for d in runs)
            wrote = sum(1 for d in runs if not d.get("readOnlyKept", True))
            den = [d.get("policyDenialCount") for d in runs if d.get("policyDenialCount") is not None]
            denied = str(sum(den)) if den else "not recorded"
            lacking = sum(1 for d in runs if 0 < sum(1 for x in (d.get("reportChecks") or {}).values() if x) < 4)
            mech += (f'<tr><td>{e(label)}</td><td class="n">{len(runs)}</td><td class="n">{passes}</td>'
                     f'<td class="n">{wrote}</td><td class="n">{denied}</td><td class="n">{lacking}</td></tr>')
        arm = f"""<h3>The arm was corrected after this ruler showed its defects, and the same runs were repeated</h3>
<div class="note"><b>Why this is here.</b> Running many models through one arm exposed faults in the arm itself, not only
in the models. They were corrected in steps and the same four models were run again each time, three runs per model, with
the same prompt and the same recorded LM Studio settings (context 100000, KV cache q8_0, temperature 0.7, top_k 20,
top_p 0.90, min_p 0, repeat penalty 1.0). <b>The first batch of corrections made the result worse</b> (v2): a safety
default refused the very build commands the task ordered. The rerun showed it, and it was corrected. Results are therefore
labelled by arm version and must not be compared across versions as if the arm were the same. The arm's code is not published.</div>
<div class="sc"><table><thead><tr><th>Model</th><th>v1 · before</th><th>v2 · first corrections</th><th>v3 · regression corrected</th><th>v4 · quoting corrected</th><th>v5 · latest outputs</th><th>v6 · closing after refusals</th><th>v7 · replan, write rule, probes</th><th>v8 · verifier, whole task</th><th>v9 · after the review</th><th>v10 · shell inspection</th></tr></thead><tbody>{vt}</tbody></table></div>
<p class="mut">v1 has no run of cyber-tiel under these exact settings; v1 for holo4 is the replication cell with the same settings.
Each cell is three runs, in order.</p>
<div class="sc"><table><thead><tr><th>Arm version</th><th>Runs</th><th>PASS</th><th>Wrote into the project</th><th>Commands refused by the read-only policy</th><th>Report with 2 or 3 of 4 facts</th></tr></thead><tbody>{mech}</tbody></table></div>
<p><b>What the tables show.</b> The pass count moves within noise from v3 to v10 (9, 8, 8, 7, 8, 6, 5 and 6 of 12; three runs per model neither show a decline nor exclude one), so the corrections cannot be
credited with a better model score. What changed is the mechanism: in v4 no run wrote into the project and the read-only
policy refused no command, where v3 had six refusals of read-only commands and v2 refused the builds the task asked for. A
correction was judged by the failure it removed, not by the pass rate. <b>v5 did not do what it was meant to</b>: giving the
report step the latest command output left the number of reports lacking a fact at 4 of 12 (the missing test count fell from 4
to 3 runs, other facts went missing instead). In v5 the policy refused 14 calls, all of them the same model asking again and
again to write a file into the read-only project in one run, which ended at the time limit: the refusal was right, and the
model had no way out of it.</p>
<p><b>v6</b> closes tool use for the rest of a step after five refused calls. It was judged against four criteria written before the
runs: no run writes into the project (met, 0 of 12); no read or build command is refused wrongly (met, one refusal in twelve
runs, a real attempt to create a source file); a closed step ends in text (not exercised: the limit was never reached, so it is
shown by a unit test and not by a live run); no clear fall in passes (met, 7 of 12 against 8 in v5). The same open faults
showed again: one run ended at the time limit after the evidence gate refused the final step three times, and the test count
was missing from two of three reports of one model.</p>
<p><b>v7</b> let a replan depend on steps already done, gave the evidence gate and the read-only policy one definition of a write
(a log written to a temp directory is not a change to the project), and kept early command output for the report step. Its four
criteria, written before the runs, were all met: no write into the project; no "files changed: none" refused because of a
temp-directory write; fewer than four reports with two or three of four facts (three); at least six passes (eight).</p>
<p><b>v8</b> corrected a real fault found by reading the logs: the lane that revises a draft was shown only the tool output of
the last step, which runs nothing, so it saw "none" and softened true reports into "unable to report"; its evidence summary
also kept the first eight items, which cut the build and the listing at the end of a task. <b>Its live result did not show the
expected effect, and its criteria were not met</b>: no write into the project (met), but one "no change" contradiction (not
examined), six reports with a fact missing against a target of at most two, and six passes against a target of eight. The
missing fact is the test total in six of twelve runs; reading the reports shows that part of this is a model listing the
per-class counts without adding them up, which the check does not accept. The check is a stricter proxy than the wording of the
task, so this measure mixes two things. The correction stays because the fault was real and a test shows it; the live data
do not show that it helped.</p>
<p><b>v9</b> carried the corrections made after the outside review (the read-only filter, the evidence gate for a report backed by a
test run, the labelling of command output, the scope of the data given to another endpoint). It was judged against four criteria
written before the runs. Met: no run wrote into the project (0 of 12); no read or build command was refused wrongly (one refusal, a
real attempt to use a writing tool). <b>Not met</b>: the evidence gate refused in at most three of twelve runs (it refused in seven,
as in v8) and at least seven passes (five). The correction to the gate for a report backed by a test run therefore did not lower the
number of refusals in live runs: that defect does not explain most of them, and their cause stays open. No correction made after the
review had, at that point, shown an effect in a live run.</p>
<p><b>v10</b> followed from a measurement, not a guess. The gate was made to report the conditions of its read-only exemption, and for a
report whose only evidence was a listing it said that no inspection had happened: its evidence text holds tool outputs, not
commands, and models inspect almost only through the shell. A shell command that writes nothing and prints something now counts as
an inspection, as it already did in the read-only policy. Criteria written before the runs: no write into the project (met, 0 of
12); the gate refused in at most three of twelve runs (<b>met</b>: two, against seven in v8 and v9, the first correction that
showed its effect live); at least seven passes (<b>not met</b>: six); no read or build command refused wrongly (met, none). The
gate is therefore not what held the pass count down. In five of the twelve runs the only missing fact is the test total, and in
four of them it is the only fact missing: a report listing the per-class counts without adding them up is scored as missing it.
The scorer is a stricter proxy than the task's wording, so most of what separates six passes from ten is a property of the
measurement, not of the arm; a scorer that accepts the per-class counts would have to be fixed beforehand and applied to every
version, and has not been written. The two refusals left (one run where the gate saw a mutation although the policy refused no
write, one where it was handed a single observation) are leads, not explanations.</p>
<div class="sc"><table><thead><tr><th>#</th><th>Defect in the arm</th><th>How it showed</th><th>Correction</th><th>State</th></tr></thead><tbody>
<tr><td>1</td><td>Bookkeeping calls (plan, report) counted as file writes by the evidence gate</td><td>A truthful "no files changed" report was refused five times in one run</td><td>Those calls are left out of the free-text write heuristic</td><td>fixed</td></tr>
<tr><td>2</td><td>A "write a file now" directive sent to a task that forbade writes</td><td>A verification step was told to write</td><td>The directive is never sent on a read-only task</td><td>fixed</td></tr>
<tr><td>3</td><td>"Do not modify any file" was only a request</td><td>Models wrote report files or unpacked artefacts into a read-only project; one used about 790k tokens</td><td>Tool-level read-only policy on by default</td><td>fixed (see 4)</td></tr>
<tr><td>4</td><td>That policy refused the builds the task ordered</td><td>A stderr merge was read as a file redirect; the dense base model went from 3 of 3 to 0 of 3</td><td>Descriptor duplication and scratch or build directories are not writes; a test for this was added</td><td>regression found by the rerun, fixed</td></tr>
<tr><td>5</td><td>A quoted character and a log under the project's own scratch directory were refused</td><td>Six refusals of read-only commands in one model's runs</td><td>Quoted text is data; a payload passed to a shell is judged on its own</td><td>fixed</td></tr>
<tr><td>6</td><td>The runner wrote a note into the project it was told not to change</td><td>One run counted as modified</td><td>The note is not written on a read-only task</td><td>fixed</td></tr>
<tr><td>7</td><td>A model that could not be loaded was reported as a protocol problem</td><td>HTTP 400 with a hint pointing at the wrong settings</td><td>A message that names memory, context and quantization</td><td>fixed</td></tr>
<tr><td>8</td><td>The final step does not receive the raw output of earlier steps</td><td>Four of twelve reports lack one fact (usually the test count) in v4 and again in v5</td><td>v5 passed the last lines of the latest commands to the report step, v7 kept the early ones too, v8 fixed the lane that revises the draft; none lowered the count of incomplete reports. Part of the measure is a stricter proxy than the task's wording (a total against per-class counts)</td><td><b>open</b>, three attempts made</td></tr>
<tr><td>9</td><td>A second replan with one step is rejected</td><td>Seen once in the early runs</td><td>A replan needs only as many steps as remain; this was already in place and has not been seen in the later runs</td><td>corrected earlier, not seen again</td></tr>
<tr><td>12</td><td>A replan that depends on steps already done is refused as "unknown step"</td><td>Accepted only on the retry, one model call lost</td><td>Dependencies on finished steps are accepted and dropped</td><td>fixed (v7)</td></tr>
<tr><td>13</td><td>The evidence gate and the read-only policy disagreed on whether a write to a temp directory changes the project</td><td>A truthful "files changed: none" was refused; the model asked to write a file to put it right and was refused again</td><td>One definition of a write for both</td><td>fixed (v7)</td></tr>
<tr><td>14</td><td>The verification lane that revises a draft saw only the last step's tool output</td><td>True reports softened into "unable to report"; the summary kept the first eight items and cut the newest</td><td>The lane gets the whole task's observations; the summary keeps up to fourteen, newest first among equals</td><td>fixed in code and by test; the live result did not show an effect (v8)</td></tr>
<tr><td>15</td><td>The read-only mark of a task lasted as long as the session</td><td>Found while preparing an outside review: after a request that forbade changes, a later "now apply the fix" in the same conversation would still have been refused</td><td>The mark belongs to the task, which a continuation or a plan step shares and a new message does not</td><td>fixed (after v8, shown by a unit test, no live run yet)</td></tr>
<tr><td>10</td><td>The evidence gate can repeat the same refusal two to four times with no way out; a step can be declared empty on an otherwise good run</td><td>Repeated refusals and "ghost" steps in v3 and v4 runs</td><td>not corrected. New data: on a read-only task the gate refused in seven of twelve v8 runs (thirteen refusals, ten of them with the reason 'claims file or content changes without evidence'; an earlier version of this page said nine, which was a miscount found by an outside review) with "claims file or content changes without evidence" and "size claim lacks current-turn evidence"</td><td><b>open</b></td></tr>
<tr><td>11</td><td>A model that keeps asking for a refused action has no way out</td><td>In one v5 run the model asked fourteen times to write a file into the read-only project and the run ended at the time limit</td><td>v6 closes tool use for the step after five refusals and tells the model to answer in text</td><td>corrected in code, shown by a unit test; not yet seen in a live run</td></tr>
</tbody></table></div>
<p><b>External review (2026-10-06).</b> An independent review of the arm and of these corrections read the sources and ran the
classification functions, without live model runs. Its verdict, in short: the corrections fix real faults, but the read-only mode
is a best-effort guard and not a guarantee that no file changes, and it should not be presented as a security boundary. It also
found that text printed by commands reaches the prompt under a heading of apparent authority, that the verification lane was
given more data than before, that the evidence gate refused a true read-only report backed by a test run, and that the public
scorer and the harness defined success slightly differently. It also found that one figure on this page was miscounted: the
evidence gate refused in seven of twelve v8 runs, not nine (corrected above). What was reproduced was corrected and is listed
below; what was not corrected is stated as open. The review itself is private because it describes ways around the guard.</p>
<div class="sc"><table><thead><tr><th>#</th><th>Raised by the review</th><th>State</th></tr></thead><tbody>
<tr><td>16</td><td>The read-only filter let some constructs through (the part of a command after a harmless pipe, a command substitution inside quotes, tools that write by name)</td><td>reproduced and corrected, with tests. The filter remains best-effort; the arm must not be described as enforcing read-only. Enforcement by the operating system, and a capability model that refuses unclassified tools, are not done</td></tr>
<tr><td>17</td><td>The evidence gate refused a true read-only report ("files changed: none, all tests pass") that rested on a real test run</td><td>reproduced and corrected, with tests; no effect on the number of refusals in the live runs of v9 (seven of twelve runs, as in v8); the cause found afterwards (a read-only shell command was not recognised as an inspection) lowered them to two of twelve in v10</td></tr>
<tr><td>18</td><td>What a command printed was placed in the prompt under a heading that said the application had recorded it</td><td>relabelled untrusted and fenced, and the step is told never to follow instructions in it. This reduces confusion; it is not a guarantee against injection</td></tr>
<tr><td>19</td><td>The verification lane received the whole task's output; another endpoint could receive it</td><td>another endpoint now receives only the current run, as before; redaction and an authorisation of what leaves the application are not done</td></tr>
<tr><td>20</td><td>The public scorer did not reject an abandoned plan, the harness did; the check is a regular expression (the literal 74, "none" anywhere)</td><td>scorer partly aligned: an abandoned plan is now rejected (no published verdict changes: every abandoned plan was already a failure), but a step that failed and was recovered still counts in the public scorer and not in the harness's own verdict field, a decision recorded in the protocol; a script reproduces this table from the data (v1 has nine runs, the others twelve); the regular-expression check is unchanged and can accept or reject a report a person would judge differently</td></tr>
</tbody></table></div>
<p class="mut">Measurement faults found on the way, all outside the arm: the first runs did not record the KV-cache type or the sampling
values; a result file was named differently from what the runner looked for when a model key held an at-sign; a vision
projector next to a model made a model not fit in memory; and a restart of the runtime's server during one batch made twelve
loads fail, so those twelve results were set aside as invalid and are not in any table.</p>
"""
    n_pass_all = sum(1 for r in repeated if r["runs"] and r["pass"] == r["runs"])
    consistent = sum(1 for r in repeated if r["repeatable"])
    return f"""
<h2 class="pb">Second ruler: live orchestration · 4 October 2026</h2>
<div class="note"><b>What this is.</b> One fixed, read-only verification task on a real project, run through a real
orchestration arm (<b>Harness Lab, primary arm</b>: plan proposal, approval, step-by-step execution, recovery, evidence gate).
It measures <b>model + harness together</b>, not coding ability, and it is not a ranking. The protocol was registered
before the confirmatory runs: <a href="https://github.com/rafaelKyra/local-llm-fieldbook/blob/main/harness/live-orchestration/PROTOCOL.md">PROTOCOL.md</a>.
Run 1 (all {len(rows)} models, one run each) was seen first and is exploratory; runs 2 and 3 repeat the
{len(cands["candidates"])} models that qualified under a rule fixed from run 1. Everything below is regenerated from
<span class="mono">data/live-orchestration-2026-10-04/</span>.</div>
<p><b>PASS</b> = the final report holds all four facts (Java version, 74 tests, APK size, "no file changed"), the project was
not touched, the session ended on its own. <b>~</b> PARTIAL = at least two facts. <b>x</b> FAIL = anything else (did not finish,
endpoint error, 10-minute timeout, wrote into the project, fewer than two facts). Bands use the same rule as the grid above:
a model joins the band while its 95% Wilson interval overlaps the band leader's. With three runs the intervals are wide, so
expect few bands; models in one band are not ranked against each other.</p>
<p><b>Repeated models.</b> {len(repeated)} models ran at least twice; {n_pass_all} passed every run; {consistent} had the same
verdict in every run. Across the {sum(causes.values())} runs of these models: {cause_text}.</p>
{fisher}
<p class="mut">{len(unavailable)} of the {len(cands["candidates"])} qualifying models ({", ".join(e(m) for m in unavailable) or "none"}) were no longer installed in
LM Studio when runs 2 and 3 were made, and keep their single run-1 result.</p>
<div class="sc"><table><thead><tr><th>Band</th>{head}</tr></thead><tbody>{rep_rows}</tbody></table></div>
<p><b>Screened once, not repeated.</b> These did not meet the repeat rule in run 1. One run is an observation, not evidence
that a model fails reproducibly.</p>
<div class="sc"><table><thead><tr>{head}</tr></thead><tbody>{once_rows}</tbody></table></div>
{addendum}
{repl}
{newm}
{arm}
<p class="mut">Did not load (excluded from rates): {inf}.</p>
<h2>Harness notes (secondary)</h2>
<p>Observations about the arm, not about the models. None was changed in order to obtain the main table above; the corrections made afterwards are in the section on the arm's iterations.</p>
<ul>
<li>The final step is handed recorded facts, and they omit raw command outputs a prompt may ask to paste (a version string,
the last lines of a build). Models either re-run the commands (a large token cost) or say they cannot verify them. That
lowers every model's report score, honest ones included.</li>
<li>"Do not modify any file" is not enforced at tool level. Several models wrote report files or unpacked a build artefact
into the project; the evidence gate noticed only when it judged the report.</li>
<li>One model family fails at once with a grammar-compiler error from the runtime (HTTP 400) before any tool runs, while a
smaller model of the same family does not. A tool with an empty-object parameter schema is a candidate cause, not tested.</li>
<li>Several models lose the plan: the proposal contains no parseable plan twice and the run continues without one.</li>
</ul>
<p class="mut">Not reproducible end to end from this repository: the arm's code is not published. The prompt, load settings,
runner, analysis, sanitiser and every run's sanitised result are.</p>
"""
