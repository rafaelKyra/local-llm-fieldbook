#!/usr/bin/env python3
"""Tables for the public-repository pilot (data/public-repo-pilot-2026-11-20/rows): per pass, per case, paired comparison, tokens. Standard library only.
usage: python3 harness/prompt-rules/public_pilot_table.py data/public-repo-pilot-2026-11-20 > data/public-repo-pilot-2026-11-20/RESULT.md"""
import collections, glob, json, os, random, statistics as st, sys
from math import comb
D = sys.argv[1]
def fisher(a, n1, c, n2):
    N, k = n1 + n2, a + c; p = lambda x: comb(n1, x) * comb(N - n1, k - x) / comb(N, k); po = p(a)
    return sum(p(x) for x in range(max(0, k - n2), min(n1, k) + 1) if p(x) <= po * (1 + 1e-9))
def sign(a, b):
    n = a + b; k = min(a, b); return min(1, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1
S, T = {}, {}
for arm in ("control", "p3f"):
    S[arm] = [json.load(open(f"{D}/rows/bench-{arm}-r{r}/summary.json")) for r in (0, 1)]
    T[arm] = {}
    for r in (0, 1):
        for f in glob.glob(f"{D}/rows/bench-{arm}-r{r}/*.json"):
            if f.endswith("summary.json"): continue
            j = json.load(open(f)); T[arm][(j["id"], r)] = j
print("# Public-repository pilot on Mercury 3: control against `p3f` (20 cases from six public repositories, 2 passes per arm)\n")
print("| arm | pass | solved | verdicts | output tokens | input tokens | tool calls | seconds |\n|---|---|---|---|---|---|---|---|")
for arm in ("control", "p3f"):
    for r, s in enumerate(S[arm]):
        print(f"| {arm} | r{r} | {s['solved']}/{s['tasks']} | {', '.join(f'{k} {v}' for k, v in sorted(s['verdicts'].items(), key=lambda x: -x[1]))} | {s['outputTokens']} | {s['inputTokens']} | {s['toolCalls']} | {s['totalSeconds']:.0f} |")
a = sum(s["solved"] for s in S["p3f"]); c = sum(s["solved"] for s in S["control"])
ids = sorted({k[0] for k in T["control"]})
pairs = collections.Counter((T["control"][k]["verdict"] == "solved", T["p3f"][k]["verdict"] == "solved") for k in T["control"])
print(f"\n**Solved:** `p3f` {a}/40 against control {c}/40 (Fisher p = {fisher(a, 40, c, 40):.3f}). Paired by case and pass: both {pairs[(True, True)]}, neither {pairs[(False, False)]}, only `p3f` {pairs[(False, True)]}, only control {pairs[(True, False)]} (sign test p = {sign(pairs[(False, True)], pairs[(True, False)]):.3f}).")
for arm in ("control", "p3f"):
    print(f"- {arm}: {sum((T[arm][(i, 0)]['verdict'] == 'solved') != (T[arm][(i, 1)]['verdict'] == 'solved') for i in ids)} of 20 cases changed outcome between its two passes")
A = [T["p3f"][k]["usage"]["outputTokens"] for k in T["p3f"]]; B = [T["control"][k]["usage"]["outputTokens"] for k in T["control"]]
random.seed(1); bs = sorted(st.mean(random.choices(A, k=len(A))) / st.mean(random.choices(B, k=len(B))) for _ in range(5000))
si = lambda arm, key: sum(s[key] for s in S[arm])
print(f"\n**Cost:** output tokens `p3f` / control {st.mean(A) / st.mean(B):.2f} (per-case bootstrap 95 % {bs[125]:.2f}-{bs[4875]:.2f}); input tokens {si('p3f', 'inputTokens') / si('control', 'inputTokens'):.2f}; tool calls {si('p3f', 'toolCalls') / si('control', 'toolCalls'):.2f}; wall time {si('p3f', 'totalSeconds') / si('control', 'totalSeconds'):.2f}.")
print("\n## Cases that are not solved by both arms in both passes\n\n| case | control r0, r1 | p3f r0, r1 |\n|---|---|---|")
for i in ids:
    cs = [T["control"][(i, r)]["verdict"] for r in (0, 1)]; ps = [T["p3f"][(i, r)]["verdict"] for r in (0, 1)]
    if cs != ["solved", "solved"] or ps != ["solved", "solved"]: print(f"| {i} | {', '.join(cs)} | {', '.join(ps)} |")
