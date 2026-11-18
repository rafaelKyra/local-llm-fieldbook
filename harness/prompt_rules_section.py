"""The prompt-rule screening as an HTML section for the public report.

Every number comes from data/prompt-rules-2026-11-18/analysis.json (written by prompt-rules/analyze.py),
so re-analysing and rebuilding cannot drift apart. Only the framing text is typed.
"""
import html, json
from pathlib import Path

e = html.escape
MODEL = {"mercury3": "Mercury-3 (hosted)", "local27b": "Qwen3.8 27B dense, Q4_K_S (LM Studio)", "strata": "Qwen3.8-Flash-Next GSQ-RCO IQ3_S (Strata)"}
ARM = {"control": "control", "p3": "closing line in system prompt", "p3f": "closing line in finish tool",
       "p4": "shortcut ledger in system prompt", "p4f": "shortcut note in finish tool", "p34": "both in system prompt"}
KIT = {"P3b": "P3b · atomic write, Windows production", "P4b": "P4b · settings loader"}


def build(data_dir: Path) -> str:
    path = data_dir / "analysis.json"
    if not path.exists():
        return ""
    a = json.loads(path.read_text(encoding="utf-8"))
    cells = {(r["model"], r["round"], r["kit"], r["arm"]): r for r in a["kit_rows"]}
    comp = {(c["model"], c["kit"], c["arm"]): c for c in a["comparisons"] if c["round"] == "round2"}
    order = {m: i for i, m in enumerate(MODEL)}
    arms = {k: i for i, k in enumerate(ARM)}

    kit_rows = ""
    for (model, rnd, kit, arm), r in sorted(cells.items(), key=lambda kv: (order[kv[0][0]], kv[0][2], arms[kv[0][3]])):
        if rnd != "round2" or kit not in KIT:
            continue
        c = comp.get((model, kit, arm))
        ci = r["behaviour_ci95"]
        d = "–" if not c or c["output_tokens_vs_control_pct"] is None else f'{c["output_tokens_vs_control_pct"]:+.0f}%'
        p = "–" if not c else ("&lt;0.001" if c["fisher_p"] < 0.001 else f'{c["fisher_p"]:.3f}')
        kit_rows += (f'<tr><td>{e(MODEL[model])}</td><td class="mono">{kit}</td><td>{e(ARM[arm])}</td><td class="n">{r["runs"]}</td>'
                     f'<td class="n">{r["solved"]}/{r["runs"]}</td><td class="n">{r["behaviour"]}/{r["runs"]}</td>'
                     f'<td class="n mut">{ci[0]:.2f}–{ci[1]:.2f}</td><td class="n">{r["mean_output_tokens"]:.0f}</td>'
                     f'<td class="n">{d}</td><td class="n">{p}</td></tr>')

    bench = {(b["model"], b["round"], b["arm"]): b for b in a["bench"]}
    bench_rows = ""
    for (model, rnd, arm), b in sorted(bench.items(), key=lambda kv: (order[kv[0][0]], kv[0][1], arms[kv[0][2]])):
        ci = b["solved_ci95"]
        bench_rows += (f'<tr><td>{e(MODEL[model])}</td><td class="mut">{rnd[-1]}</td><td>{e(ARM[arm])}</td><td class="n">{b["passes"]}</td>'
                       f'<td class="n">{b["solved"]}/{b["tasks"]}</td><td class="n mut">{ci[0]:.2f}–{ci[1]:.2f}</td>'
                       f'<td class="n">{b["output_tokens"]:,}</td></tr>')

    return f"""
<h2 class="pb">Third ruler: one-line prompt rules · 18 November 2026</h2>
<p>Two candidate rules for the agent's instructions, each a single line, tested as arms against a control on three models.
<b>Closing line (P3):</b> before finishing, name what was skipped or not checked and any risk. <b>Shortcut ledger (P4):</b> mark a
shortcut in the code as <span class="mono">shortcut: what; upgrade when condition</span> and record it in <span class="mono">DEBT.md</span>.
Each rule was placed in the system prompt and, in a second arm, in the description of the <span class="mono">finish</span> tool.
Each kit is one small task with a hidden check run after the agent finished: <b>solved</b> (the work is right, including one behaviour the
visible tests do not cover) and <b>behaviour</b> (the rule's effect shows). Cost is output tokens per run against the control.</p>
<div class="sc"><table><thead><tr><th>Model</th><th>Kit</th><th>Arm</th><th>Runs</th><th>Solved</th><th>Behaviour</th><th>95% interval</th><th>Out tokens</th><th>vs control</th><th>Fisher p</th></tr></thead><tbody>{kit_rows}</tbody></table></div>
<p class="mut">Behaviour counts runs that were solved and showed the effect. Fisher p is two-sided against the control of the same model and kit, with no
correction for the many comparisons here. 20 to 30 runs per cell on the hosted model and Strata, 10 on the local 27B.</p>

<p><b>Does the rule cost solved tasks?</b> The full 38-task bench (30 basic and 8 specification tasks), repeated, hosted model; the control rows are
from the first round with the same seeds. The two rounds ran on different days.</p>
<div class="sc"><table><thead><tr><th>Model</th><th>Round</th><th>Arm</th><th>Passes</th><th>Solved</th><th>95% interval</th><th>Output tokens</th></tr></thead><tbody>{bench_rows}</tbody></table></div>

<h3>What it shows</h3>
<ul>
<li><b>The closing line works when it sits in the finish tool, not when it sits in the system prompt.</b> On Mercury-3 the system-prompt version
is indistinguishable from the control (21/30 against 22/30); the finish-tool version reaches 29/30. On the local 27B dense the control never wrote
such a line (0/10), the system-prompt version did 7/10, the finish-tool version 10/10. On Flash-Next the control already did it 18/20, so the check
has no room there.</li>
<li><b>It did not cost solved tasks.</b> Every cell of the valid kits is fully solved, and on the 38-task bench the finish-tool arm matches the control (109/114).
Output tokens move from about −3% (bench, hosted) to about +20% on the local 27B, where the added sentences are most of the difference.</li>
<li><b>The shortcut ledger was not followed by any model:</b> 0 of 60 runs on Mercury-3 (30 with the rule in the system prompt, 30 in the finish tool), 0 of 40 on Flash-Next (20 and 20), 0 of 10 on the local 27B (system prompt only). These models do not
label their own simplifications, even when the rule is in the tool they must call to finish. Nothing here says the idea is bad; it says one line does not
make these models do it.</li>
</ul>

<div class="bad-note"><b>Withdrawn.</b> The first round used kits that could not show the behaviour (P3: the models kept the input validation, so nothing was given up;
P4: the task was a one-line bug fix that needs no shortcut), and a first version of the P4b check required whitespace handling the task never stated. Those rows
are kept under <span class="mono">rows/…/round1</span> and <span class="mono">round2-p4b-v1-withdrawn</span> and are excluded from the tables above. See
<a href="https://github.com/rafaelKyra/local-llm-fieldbook/blob/main/CORRECTIONS.md">CORRECTIONS.md</a> item 10.</div>

<h3>Limits of this ruler</h3>
<ul>
<li>One task per kit. P3b asks for an atomic write on a Windows server the agent cannot test; the closing line is checked by keywords in the last five lines (for example "not verified", "assume", "risk"), which a strong model can meet by habit — the control is already 22/30 on Mercury-3.</li>
<li>Almost everything is solved, so the ruler measures the behaviour, not the ability. It says nothing about harder tasks or about a dense model with a long thinking budget.</li>
<li>On the local 27B the two repetitions of the bench gave identical numbers (a fixed seed); they count as one pass, not two independent ones.</li>
<li>Flash-Next thinks long (about 4,000 output tokens per kit run against 1,000 on the others), so its token differences between arms include thinking noise.</li>
<li>Model builds, rule texts, scripts and every run row are in <span class="mono">data/prompt-rules-2026-11-18/</span>; the Forge agent core the runs used is not published, so the drivers show the method and the numbers can be re-analysed, but the runs cannot be repeated from this repository alone.</li>
</ul>
"""
