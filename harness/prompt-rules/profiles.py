#!/usr/bin/env python3
"""Behavioural profile of every model that has kit rows (kits P3b and P3c, arms control and p3f), computed from the rows in data/prompt-rules-2026-11-18 and data/prompt-rules-2026-11-19 with ONE definition for all models.
Standard library only. Usage: python3 harness/prompt-rules/profiles.py > data/prompt-rules-2026-11-19/profiles.md
Definitions (per run): solved = the hidden check of the kit passes (the work is right); status 'completed' = the agent's own verification gate saw a passing check before it finished,
'unverified' = it delivered without one (the stored row does not say why); line = the final summary contains a sentence on what was skipped or not verified (kit check, behaviour flag).
Runs with status 'interrupted' (cut off by the endpoint) are excluded; every other status counts."""
import glob, json, os, random, statistics as st
from math import comb
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"); D18 = os.path.join(DATA, "prompt-rules-2026-11-18", "rows"); D19 = os.path.join(DATA, "prompt-rules-2026-11-19", "rows")
# label, host, [(round dir, model dir, kits)]
SRC = [
 ("Mistral-Small-3.2 24B (BF16)", "Berget", [(D19, "berget-mistralai_Mistral-Small-3.2-24B-Instruct-2506", "round10", "PB")]),
 ("Gemma-4-31B-it (BF16)", "Berget", [(D19, "berget-google_gemma-4-31B-it", "round10", "PB")]),
 ("GLM-5.3-Flash (FP8)", "Berget", [(D19, "berget-zai-org_GLM-5.3-Flash", "round10", "PB")]),
 ("GLM-5.3-Flash", "OpenRouter", [(D19, "or-paid-z-ai_glm-5.3-flash", "round7", "PB")]),
 ("deepseek-v4.1-flash", "OpenRouter", [(D19, "or-paid-deepseek_deepseek-v4.1-flash-1017", "round7", "PB")]),
 ("Qwen3.8-Flash", "OpenRouter", [(D19, "or-paid-qwen_qwen3.8-flash", "round7", "PB")]),
 ("Qwen3.8-27B", "OpenRouter", [(D19, "or-paid-qwen_qwen3.8-27b", "round7", "PB")]),
 ("Qwen3.7-Flash", "OpenRouter", [(D19, "or-paid-qwen_qwen3.7-flash", "round7", "PB")]),
 ("Qwen3-Coder-Next", "OpenRouter", [(D19, "or-paid-qwen_qwen3-coder-next", "round7", "PB")]),
 ("gpt-oss-120b", "OpenRouter", [(D19, "or-paid-openai_gpt-oss-120b", "round7", "PB")]),
 ("GLM-4.7-Flash", "OpenRouter", [(D19, "or-paid-z-ai_glm-4.7-flash", "round7", "PB")]),
 ("Claude Haiku 5.5", "OpenRouter", [(D19, "or-paid-anthropic_claude-haiku-5.5", "round7", "PB")]),
 ("Nemotron-3-Ultra 550B", "OpenRouter free", [(D19, "or-free-nvidia_nemotron-3-ultra-550b-a55b_free", "round6", "PB")]),
 ("Mercury 3", "Inception", [(D19, "mercury-3", "round11", "PB")]),
 ("Strata (Qwen3.8-Flash-Next IQ3_S)", "local", [(D18, "strata", "round2", "B"), (D19, "strata", "round3", "C")]),
 ("Qwen3.8-27B distil (local)", "local", [(D18, "local27b", "round2", "B")]),
 ("OxCoder 9B Q4_K_S", "local", [(D19, "oxcoder-9b-q4ks", "round4", "PB")]),
]
def fisher(a, n1, c, n2):
    if n1 == 0 or n2 == 0: return float("nan")
    N, k = n1 + n2, a + c
    p = lambda x: comb(n1, x) * comb(N - n1, k - x) / comb(N, k)
    po = p(a); return sum(p(x) for x in range(max(0, k - n2), min(n1, k) + 1) if p(x) <= po * (1 + 1e-9))
def rows(spec):
    out = {"control": [], "p3f": []}
    for base, m, rd, kits in spec:
        for f in sorted(glob.glob(os.path.join(base, m, rd, "*.json"))):
            j = json.load(open(f))
            if j.get("status") == "interrupted" or j["arm"] not in out: continue
            if (j["kit"] == "P3b" and "B" in kits) or (j["kit"] == "P3c" and "C" in kits) or (j["kit"] in ("P3b", "P3c") and kits == "PB"): out[j["arm"]].append(j)
    return out
def pc(k, n): return f"{100 * k / n:.0f} %" if n else "-"
P = []
for label, host, spec in SRC:
    R = rows(spec); c, p = R["control"], R["p3f"]
    if not c or not p: continue
    P.append((label, host, c, p))
print("# Behavioural profile of every model with kit rows (kits P3b + P3c, control arm = the model as it is, p3f arm = with the closing-line sentence)\n")
print("Same definition for all models (see the script header). Statistics are Fisher exact two-sided without correction; hosts, quantisations and sample sizes differ, so the table describes, it does not rank.\n")
print("## Table 1: what the model does by itself (control arm)\n")
print("| model | host | runs (control / p3f) | work right (hidden check) | verifies itself (status completed) | right but delivered unverified | mean model calls | mean output tokens | writes the closing line unprompted |\n|---|---|---|---|---|---|---|---|---|")
for label, host, c, p in P:
    n = len(c); sol = sum(bool(r["solved"]) for r in c); ver = sum(r["status"] == "completed" for r in c)
    ru = sum(r["status"] != "completed" and bool(r["solved"]) for r in c); nv = n - ver
    ln = sum(bool(r["behaviour"]) for r in c)
    print(f"| {label} | {host} | {n} / {len(p)} | {sol}/{n} ({pc(sol, n)}) | {ver}/{n} ({pc(ver, n)}) | {ru}/{nv if nv else 0} | {st.mean(r['usage']['modelCalls'] for r in c):.1f} | {st.mean(r['usage']['outputTokens'] for r in c):.0f} | {ln}/{n} ({pc(ln, n)}) |")
print("\n## Table 2: what the rule changes (p3f against control)\n")
print("| model | closing line control -> p3f | p | work right control -> p3f | verifies itself control -> p3f | output tokens p3f / control (95 % CI) | reading |\n|---|---|---|---|---|---|---|")
random.seed(1)
for label, host, c, p in P:
    n, m = len(c), len(p)
    a = sum(bool(r["behaviour"]) for r in p); b = sum(bool(r["behaviour"]) for r in c); pv = fisher(a, m, b, n)
    sp = sum(bool(r["solved"]) for r in p); sc = sum(bool(r["solved"]) for r in c)
    vp = sum(r["status"] == "completed" for r in p); vc = sum(r["status"] == "completed" for r in c)
    A = [r["usage"]["outputTokens"] for r in p]; B = [r["usage"]["outputTokens"] for r in c]
    bs = sorted(st.mean(random.choices(A, k=len(A))) / max(1, st.mean(random.choices(B, k=len(B)))) for _ in range(2000))
    if pv < 0.01 and a > b: rd = "rule works"
    elif pv < 0.05 and a > b: rd = "rule works (weaker)"
    elif a >= m * 0.9 and b >= n * 0.9: rd = "writes the line anyway (ceiling)"
    elif a <= m * 0.1 and b <= n * 0.1: rd = "never writes it (nothing to change)"
    else: rd = "no clear effect"
    print(f"| {label} | {b}/{n} -> {a}/{m} | {pv:.4f} | {sc}/{n} -> {sp}/{m} | {vc}/{n} -> {vp}/{m} | {st.mean(A) / st.mean(B):.2f} ({bs[50]:.2f}-{bs[1950]:.2f}) | {rd} |")
print("\n## Profile types (control arm: verifies itself? writes the line unprompted?)\n")
typ = {}
for label, host, c, p in P:
    n = len(c); ver = sum(r["status"] == "completed" for r in c) / n; ln = sum(bool(r["behaviour"]) for r in c) / n
    t = ("verifies" if ver >= 0.7 else "mostly does not verify" if ver < 0.4 else "sometimes verifies") + " / " + ("speaks unprompted" if ln >= 0.7 else "silent" if ln <= 0.3 else "speaks sometimes")
    typ.setdefault(t, []).append(label)
for t, v in sorted(typ.items()): print(f"- **{t}:** " + "; ".join(v))
# ---- exploratory (NOT planned beforehand; 16 models, many possible comparisons: read as hypotheses) ----
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):  # average ranks for ties
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        for k in range(i, j + 1): r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r
def spearman(a, b):
    ra, rb = rank(a), rank(b); ma, mb = st.mean(ra), st.mean(rb)
    return sum((u - ma) * (v - mb) for u, v in zip(ra, rb)) / (sum((u - ma) ** 2 for u in ra) * sum((v - mb) ** 2 for v in rb)) ** 0.5
U = [(l, c) for l, h, c, p in P if l != "GLM-5.3-Flash (FP8)"]  # the Berget copy of GLM-5.3-Flash would count one model twice
x = [st.mean(r["usage"]["outputTokens"] for r in c) for _, c in U]; y = [sum(bool(r["behaviour"]) for r in c) / len(c) for _, c in U]; z = [st.mean(r["usage"]["modelCalls"] for r in c) for _, c in U]
print("\n## Exploratory notes (not planned beforehand)\n")
print(f"- Across {len(U)} models (GLM-5.3-Flash counted once), Spearman correlation between mean output tokens per run and the share of runs that write the closing line unprompted: **{spearman(x, y):.2f}**; with mean model calls per run: {spearman(z, y):.2f}. Models that write more per run tend to report what they skipped on their own. Output-token counts may not include hidden reasoning for every host, so this is a description of the kits, not a law.")
for l, h, c, p in P:
    vc = sum(r["status"] == "completed" for r in c); vp = sum(r["status"] == "completed" for r in p)
    if fisher(vp, len(p), vc, len(c)) < 0.15 and vp != vc:
        print(f"- Verification habit with the rule: {l}: {vc}/{len(c)} -> {vp}/{len(p)} (p = {fisher(vp, len(p), vc, len(c)):.3f}); one of many comparisons, not a finding.")
