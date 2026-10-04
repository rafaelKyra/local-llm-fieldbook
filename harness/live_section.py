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
<p class="mut">Did not load (excluded from rates): {inf}.</p>
<h2>Harness notes (secondary)</h2>
<p>Observations about the arm, not about the models. None was changed in order to obtain the table above.</p>
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
