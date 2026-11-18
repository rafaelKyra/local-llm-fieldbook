#!/usr/bin/env python3
"""Analyse the prompt-rule screening. usage: analyze.py [data-dir]  (default data/prompt-rules-2026-11-18)

Reads rows/<model>/<round>/<kit>.<arm>.<rep>.json (one agent run each, written by kitrun.mjs) and
bench/<model>/<round>/bench-<arm>-r<N>.summary.json (one full pass of the 38-task bench).
Writes analysis.json, which prompt_rules_section.py renders; nothing on the page is typed by hand except framing text.
Standard library only.
"""
import glob, json, os, sys
from math import comb, sqrt
from pathlib import Path

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "data" / "prompt-rules-2026-11-18"
ARMS = ["control", "p3", "p3f", "p4", "p4f", "p34"]
WITHDRAWN = {("round1", "P3"), ("round1", "P4"), ("round2-p4b-v1-withdrawn", "P4b")}  # see CORRECTIONS 10


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


def fisher(a, n1, b, n2):
    """Two-sided Fisher exact p for a/n1 versus b/n2 successes."""
    k, n = a + b, n1 + n2
    def pr(x):
        return comb(n1, x) * comb(n2, k - x) / comb(n, k)
    p0 = pr(a)
    return round(sum(pr(x) for x in range(max(0, k - n2), min(n1, k) + 1) if pr(x) <= p0 + 1e-12), 4)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 1) if xs else None


kits = {}
for f in sorted(glob.glob(str(DATA / "rows" / "*" / "*" / "*.json"))):
    model, rnd = f.split(os.sep)[-3:-1]
    r = json.load(open(f, encoding="utf-8"))
    kits.setdefault((model, rnd, r["kit"], r["arm"]), []).append(r)

kit_rows = []
for (model, rnd, kit, arm), rs in sorted(kits.items()):
    n = len(rs)
    sol = sum(1 for r in rs if r["solved"])
    beh = sum(1 for r in rs if r["solved"] and r["behaviour"])
    kit_rows.append({
        "model": model, "round": rnd, "kit": kit, "arm": arm, "withdrawn": (rnd, kit) in WITHDRAWN,
        "runs": n, "solved": sol, "behaviour": beh, "behaviour_ci95": wilson(beh, n),
        "mean_output_tokens": mean([(r.get("usage") or {}).get("outputTokens") for r in rs]),
        "mean_seconds": mean([r.get("seconds") for r in rs]),
        "mean_reply_chars": mean([r.get("replyChars") for r in rs]),
        "crashes": sum(1 for r in rs if r.get("crash")),
    })

index = {(r["model"], r["round"], r["kit"], r["arm"]): r for r in kit_rows}
comparisons = []
for (model, rnd, kit, arm), r in sorted(index.items()):
    if arm == "control" or r["withdrawn"]:
        continue
    c = index.get((model, rnd, kit, "control"))
    if not c:
        continue
    cost = None
    if c["mean_output_tokens"] and r["mean_output_tokens"]:
        cost = round(100 * (r["mean_output_tokens"] / c["mean_output_tokens"] - 1), 1)
    comparisons.append({
        "model": model, "round": rnd, "kit": kit, "arm": arm,
        "behaviour": f'{r["behaviour"]}/{r["runs"]}', "control_behaviour": f'{c["behaviour"]}/{c["runs"]}',
        "fisher_p": fisher(r["behaviour"], r["runs"], c["behaviour"], c["runs"]),
        "solved": f'{r["solved"]}/{r["runs"]}', "control_solved": f'{c["solved"]}/{c["runs"]}',
        "output_tokens_vs_control_pct": cost,
    })

bench = {}
for f in sorted(glob.glob(str(DATA / "bench" / "*" / "*" / "*.summary.json"))):
    model, rnd = f.split(os.sep)[-3:-1]
    arm = os.path.basename(f).split("-")[1]
    s = json.load(open(f, encoding="utf-8"))
    a = bench.setdefault((model, rnd, arm), {"passes": 0, "tasks": 0, "solved": 0, "output_tokens": 0, "input_tokens": 0, "seconds": 0.0})
    a["passes"] += 1; a["tasks"] += s["tasks"]; a["solved"] += s["solved"]
    a["output_tokens"] += s["outputTokens"]; a["input_tokens"] += s["inputTokens"]; a["seconds"] = round(a["seconds"] + s["totalSeconds"], 1)
bench_rows = []
for (model, rnd, arm), a in sorted(bench.items()):
    bench_rows.append({"model": model, "round": rnd, "arm": arm, **a, "rate": round(a["solved"] / a["tasks"], 3), "solved_ci95": wilson(a["solved"], a["tasks"])})

out = {"kit_rows": kit_rows, "comparisons": comparisons, "bench": bench_rows,
       "note": "behaviour counts runs that were solved AND showed the behaviour; fisher_p is two-sided on behaviour counts of all runs vs control; no multiple-comparison correction."}
(DATA / "analysis.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"{len(kit_rows)} kit cells, {len(comparisons)} comparisons, {len(bench_rows)} bench cells -> {DATA / 'analysis.json'}")
