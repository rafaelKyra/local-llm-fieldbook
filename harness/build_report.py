#!/usr/bin/env python3
"""Build the public report (docs/index.html) from the measurement data.

Nothing in the report is typed by hand except the framing text: every number comes from
scores.json, task-rates.json and task1-failure-modes.json, so re-scoring and rebuilding
cannot drift apart.

Usage: python3 harness/build_report.py [DATA_DIR] [OUT_HTML]
"""
import html, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_section

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "grid-2026-09-20"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "docs" / "index.html"
e = html.escape

rows = json.loads((DATA / "scores.json").read_text(encoding="utf-8"))
modes = json.loads((DATA / "task1-failure-modes.json").read_text(encoding="utf-8"))
published = json.loads((DATA / "task-rates.json").read_text(encoding="utf-8"))
answers = {}
for p in sorted((DATA / "answers").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    answers[d["model"]] = d
titles = {}
for d in answers.values():
    for n, a in d["answers"].items():
        titles.setdefault(int(n), a.get("title", f"Task {n}"))

N = len(rows)
bands_n = max(r["band"] for r in rows)
in_band1 = sum(1 for r in rows if r["band"] == 1)
incomplete_n = sum(r["incomplete"] for r in rows)
counted_as_pass = sum(r["lenient_pass"] - r["pass"] for r in rows)
reasons = {}
for m in modes.values():
    reasons[m["reason"]] = reasons.get(m["reason"], 0) + 1
failing = [m for m in modes.values() if m["reason"] != "pass"]
sed_n = sum(m["sed_in_run_command"] for m in failing)

SYM = {"pass": ("P", "ok"), "fail": ("·", "bad"), "incomplete": ("?", "warn")}


def cell(states: list[str]) -> str:
    if len(states) == 1:
        s, c = SYM[states[0]]
        return f'<td class="c {c}">{s}</td>'
    k = states.count("pass")
    c = "ok" if k == len(states) else ("bad" if k == 0 else "warn")
    return f'<td class="c {c}">{k}/{len(states)}</td>'


def short(model: str) -> str:
    return model if len(model) <= 46 else model[:44] + "…"


band_rows = "".join(
    f'<tr><td class="n">{r["band"]}</td><td class="mono">{e(short(r["model"]))}</td>'
    f'<td class="n">{r["pass"]}</td><td class="n">{r["fail"]}</td><td class="n">{r["incomplete"]}</td>'
    f'<td class="n">{r["rate"]:.2f}</td><td class="n">{r["ci95"][0]:.2f}–{r["ci95"][1]:.2f}</td>'
    f'<td class="n">{r["ceiling"]:.2f}</td><td class="n mut">{r["lenient_pass"]}</td></tr>'
    for r in rows)

head_cells = "".join(f'<th class="c">{t}</th>' for t in range(1, 15))
matrix_rows = "".join(
    f'<tr><td class="mono">{e(short(r["model"]))}</td>'
    + "".join(cell(r["per_task"][str(t)]) for t in range(1, 15)) + "</tr>"
    for r in rows)

task_rows = ""
for t in range(1, 15):
    ps = sum(r["per_task"][str(t)].count("pass") for r in rows)
    inc = sum(r["per_task"][str(t)].count("incomplete") for r in rows)
    pub = published[str(t)]
    task_rows += (f'<tr><td class="n">{t}</td><td>{e(titles.get(t, ""))}</td>'
                  f'<td class="n">{ps}/{N}</td><td class="n">{inc}</td>'
                  f'<td class="n mut">{pub["passed"]}/{pub["of"]}</td></tr>')

reason_rows = "".join(f'<tr><td>{e(k)}</td><td class="n">{v}</td></tr>'
                      for k, v in sorted(reasons.items(), key=lambda x: -x[1]))


def first_answer(model_prefix: str) -> str:
    for m, d in answers.items():
        if m.startswith(model_prefix):
            t = d["answers"]["1"].get("text", "")
            import re
            return re.sub(r"<think>.*?</think>", "", t, flags=re.S).strip()[:520]
    return ""


fail_ex = first_answer("qwen3.8-27b@q5_k_m")
pass_ex = first_answer("dirk-qwen3.8-27b")

CSS = """
@page{size:A4;margin:10mm}
:root{--ink:#0a0a0a;--mut:#666;--line:#ddd;--soft:#f8f8f8;--accent:#1a5490;--ok:#2d8659;--warn:#b8860b;--bad:#c41e3a;--mono:'SF Mono',Monaco,Consolas,monospace}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{color:var(--ink);font:9.5pt/1.5 -apple-system,'Segoe UI',sans-serif;padding:18px;max-width:900px;margin:0 auto;background:#fff}
header{border-bottom:3px solid var(--ink);padding-bottom:2mm;margin-bottom:4mm}
h1{font-size:16pt;font-weight:800;letter-spacing:-.5pt}
.rig{display:flex;gap:3mm;font-size:8pt;color:var(--mut);margin-top:1.5mm;flex-wrap:wrap}.rig b{color:var(--ink)}
h2{font-size:11pt;margin:5mm 0 2mm;font-weight:700;border-bottom:1px solid var(--line);padding-bottom:.8mm}
p{margin:1.5mm 0}
a{color:var(--accent);text-decoration:none;border-bottom:1px dotted var(--accent)}
.sc{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:7.8pt;margin:2mm 0 3mm}
th,td{border:.5pt solid var(--line);padding:1.1mm 1.4mm;text-align:left;vertical-align:top}
th{background:var(--soft);font-size:7pt;text-transform:uppercase;letter-spacing:.3pt;font-weight:600}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
td.c,th.c{text-align:center;padding:1mm .6mm;width:5.2mm}
td.ok{background:#e8f8f0;color:var(--ok);font-weight:700}td.bad{background:#fdecef;color:var(--bad)}td.warn{background:#fff6dd;color:var(--warn);font-weight:700}
.mono,pre{font-family:var(--mono);font-size:7.3pt}.mut{color:var(--mut)}
pre{background:var(--soft);border:.5pt solid var(--line);padding:2mm;margin:1.5mm 0;white-space:pre-wrap;word-break:break-word}
.note{background:#fff9e6;border-left:3px solid var(--warn);padding:2mm 3mm;margin:2mm 0;font-size:8.5pt;border-radius:1mm}.note b{color:var(--warn)}
.tip{background:#e8f8f0;border-left:3px solid var(--ok);padding:2mm 3mm;margin:2mm 0;font-size:8.5pt;border-radius:1mm}.tip b{color:var(--ok)}
.bad-note{background:#fdecef;border-left:3px solid var(--bad);padding:2mm 3mm;margin:2mm 0;font-size:8.5pt;border-radius:1mm}.bad-note b{color:var(--bad)}
.tag{display:inline-block;font-size:7pt;padding:.7mm 2mm;border:.5pt solid var(--line);border-radius:1mm;white-space:nowrap}
.tag.ok{border-color:var(--ok);color:var(--ok)}.tag.warn{border-color:var(--warn);color:var(--warn)}
ul{margin:1.5mm 0 1.5mm 5mm}li{margin:.7mm 0}
footer{margin-top:5mm;padding-top:3mm;border-top:1px solid var(--line);font-size:7.5pt;color:var(--mut)}
.pb{page-break-before:always}
"""

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fieldbook · Grid of 20 September 2026 · {N} builds, 14 tasks, one run</title>
<meta name="description" content="Re-scorable measurements of {N} local LLM builds on a 14-task coding grid, with three-state scoring, bands instead of rankings, and a log of what was retracted.">
<style>{CSS}</style></head><body>
<header>
<h1>Fieldbook · Grid of 20 September 2026</h1>
<div class="rig"><span><b>Builds:</b> {N}</span><span><b>Tasks:</b> 14</span><span><b>Runs:</b> 1 per build</span>
<span><b>Rig:</b> dual Xeon E5-2680 v4 · 192 GB DDR4 ECC · RTX 3090 24 GB</span><span><b>Runtime:</b> LM Studio</span></div>
</header>

<div class="note"><b>How to read this page.</b> Everything below is regenerated from the saved data in
<span class="mono">data/grid-2026-09-20/</span> and <span class="mono">data/live-orchestration-2026-10-04/</span> by
<span class="mono">harness/build_report.py</span>; none of it is typed by hand but the framing text. Measurements and field notes are kept apart: a field note can be right and still not be a measurement.
Models are grouped in <b>bands</b>, never ranked by position.</div>

<h2>What the data shows</h2>
<table><thead><tr><th>#</th><th>Finding</th><th>Status</th></tr></thead><tbody>
<tr><td class="n">1</td><td>A 14-task, single-run grid <b>cannot rank</b> these builds. {in_band1} of {N} fall in one band; {N - in_band1} separate{'s' if N - in_band1 == 1 else ''} from the rest.</td><td><span class="tag ok">reproducible</span></td></tr>
<tr><td class="n">2</td><td><b>Truncation moves scores.</b> {incomplete_n} task results are incomplete (cut off at the token cap, or errored). {counted_as_pass} of them satisfied a rule on their visible text and used to be counted as passes. They are now unknown, not passes.</td><td><span class="tag ok">reproducible</span></td></tr>
<tr><td class="n">3</td><td><b>Task 1 does not measure obedience to a tool contract.</b> The model is never told the sequence it is scored against. Of {len(failing)} failing answers, {sed_n} contain <span class="mono">sed</span> and most never emit <span class="mono">write_file</span>.</td><td><span class="tag ok">reproducible</span></td></tr>
<tr><td class="n">4</td><td>Where builds differ, they differ <b>by task</b>, not along a single axis (matrix below).</td><td><span class="tag ok">reproducible</span></td></tr>
</tbody></table>

<h2>Bands, not positions</h2>
<p>Sorted by passes out of <i>all</i> tasks: an incomplete answer counts against, because a build that cannot finish a task
inside the cap has not delivered it. The <b>ceiling</b> is the rate if every incomplete answer had passed. A build joins the
current band while its 95% Wilson interval overlaps its band leader's. The interval reflects only which 14 tasks were chosen;
run-to-run noise needs repeated runs. Builds in one band are <b>not</b> ranked against each other.</p>
<div class="sc"><table><thead><tr><th>Band</th><th>Build</th><th>Pass</th><th>Fail</th><th>Inc.</th><th>Rate</th><th>95% interval</th><th>Ceiling</th><th title="visible-text convention of the earlier table">Old*</th></tr></thead><tbody>{band_rows}</tbody></table></div>
<p class="mut">* "Old" counts an incomplete answer as a pass when its visible text satisfies the rule. It is what the earlier hand-written table used, shown for continuity only.</p>

<h2 class="pb">Build × task</h2>
<p><span class="tag ok">P</span> passed · <span class="tag">·</span> failed · <span class="tag warn">?</span> incomplete (cut off or errored). Rows keep band order; read across a row, not down to a rank.</p>
<div class="sc"><table><thead><tr><th>Build</th>{head_cells}</tr></thead><tbody>{matrix_rows}</tbody></table></div>
<div class="sc"><table><thead><tr><th>#</th><th>Task</th><th>Pass</th><th>Incomplete</th><th title="earlier table">Old*</th></tr></thead><tbody>{task_rows}</tbody></table></div>

<h2>Task 1, examined</h2>
<p><b>Task 1 — {e(titles.get(1, ''))}.</b> The prompt asks for "the exact tool-call sequence" to find Python files importing
<span class="mono">requests</span> and replace <span class="mono">requests.get</span> with <span class="mono">httpx.get</span>.
The scoring rule requires search → read → write. That sequence appears only in the hidden pass criteria; the runner removes
them before the prompt is sent.</p>
<div class="sc"><table><thead><tr><th>What the answer did</th><th>Builds</th></tr></thead><tbody>{reason_rows}</tbody></table></div>
<p>A failing answer from <span class="mono">qwen3.8-27b@q5_k_m</span> — one command, which does what the request says:</p>
<pre>{e(fail_ex)}</pre>
<p>A passing answer from <span class="mono">dirk-qwen3.8-27b</span>:</p>
<pre>{e(pass_ex)}</pre>
<div class="bad-note"><b>Withdrawn.</b> The earlier claims that models "violate an explicit instruction" or "route around a tool
contract" are not supported: the instruction was never given. Task 1 measures agreement with a hidden reference sequence.
See <a href="https://github.com/rafaelKyra/local-llm-fieldbook/blob/main/CORRECTIONS.md">CORRECTIONS.md</a>.</div>

<h2>Reported earlier, not yet reproduced</h2>
<p>From a previous hand-written report; the raw data is not in this repository. Treat these as claims.</p>
<ul>
<li>A 4,096-token cap turned a 13/14 build into 7/14 on the same text.</li>
<li>Some GGUF chat templates reject a separate <span class="mono">system</span> parameter, so the Anthropic Messages API fails on them while the OpenAI-style API works.</li>
<li>Without <span class="mono">--gpu max</span>, LM Studio can silently split a model between GPU and CPU.</li>
<li>Executable repair of six real defects from a private repository: 0 valid fixes in 30 runs. The cases stay private; the method and results will be published.</li>
</ul>

{live_section.build(ROOT / "data" / "live-orchestration-2026-10-04")}

<h2>Limits</h2>
<ul>
<li>One machine; speeds do not transfer. The grid has one run per build; the live-orchestration ruler repeats the models it qualifies.</li>
<li>Model files are community builds with unstable names, and file hashes are not yet recorded.</li>
<li>Pass rules are keyword and structure checks, not execution. A pass is not a verified solution.</li>
<li>The saved answers are outputs of third-party models, each under its own license; the author claims no rights over them.</li>
</ul>

<h2>Reproduce</h2>
<pre>python3 harness/score_grid.py data/grid-2026-09-20/answers
python3 harness/task1_failure_modes.py data/grid-2026-09-20/answers --json data/grid-2026-09-20/task1-failure-modes.json
python3 harness/build_report.py</pre>
<p>No GPU needed. To add runs: <span class="mono">RUNS=3 harness/run_all.sh &lt;model-key&gt;</span>.</p>

<footer>Model names are trademarks of their owners and appear only to identify what was tested; no affiliation or endorsement is implied. “Fieldbook” here means a notebook of dated field notes, not a product. · Fieldbook · code Apache-2.0, text and results CC BY 4.0 (saved model outputs excluded) · Copyright 2026 Rafael Kyra ·
<a href="https://github.com/rafaelKyra/local-llm-fieldbook">source</a> · <a href="https://github.com/rafaelKyra/local-llm-fieldbook/blob/main/CORRECTIONS.md">corrections</a></footer>
</body></html>
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT} ({len(page.encode())} bytes): {N} builds, {bands_n} bands")
