#!/usr/bin/env python3
"""Recomputes the head-to-head comparisons (cmp1, cmp2) from the sanitised data, by the rules frozen before each run.

Usage: comparisons.py <data-dir>     (the folder that holds comparisons/)

Success is the scorer-3 verdict (analyze.verdict); two-sided Fisher exact test on PASS counts. Latency: elapsedSeconds, medians.
Runs without a result file (interrupted) are not in the data and are never counted as failures. Nothing here is merged
across prompts or across comparisons.
"""
import glob, importlib.util, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("analyze", os.path.join(HERE, "analyze.py"))
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)
TAGS = ["base27", "gsq", "cyber", "holo4"]


def fisher(a, b, c, d):
    n = a + b + c + d; r1, r2, c1 = a + b, c + d, a + c
    lc = lambda n_, k_: math.lgamma(n_ + 1) - math.lgamma(k_ + 1) - math.lgamma(n_ - k_ + 1)
    p = lambda x: math.exp(lc(r1, x) + lc(r2, c1 - x) - lc(n, c1))
    po = p(a)
    return min(1.0, sum(p(x) for x in range(max(0, c1 - r2), min(r1, c1) + 1) if p(x) <= po * (1 + 1e-9)))


def load(folder):
    runs = []
    for tag in TAGS:
        for f in sorted(glob.glob(os.path.join(folder, f"{tag}-run*", "*.json"))):
            d = json.load(open(f)); runs.append((tag, d))
    return runs


def summarise(name, runs):
    v = [analyze.run_verdict(d) for _, d in runs]
    el = [d.get("elapsedSeconds") for _, d in runs if d.get("elapsedSeconds") is not None]
    wrote = sum(1 for _, d in runs if not d.get("readOnlyKept", True))
    cells = {t: "".join({"PASS": "P", "PARTIAL": "~", "FAIL": "x"}.get(analyze.run_verdict(d), "?") for tt, d in runs if tt == t) for t in TAGS}
    print(f"  {name:28s} runs {len(runs):2d}  PASS {v.count('PASS'):2d}  wrote {wrote}  median {statistics.median(el) if el else None} s  {cells}")
    return v.count("PASS"), len(runs)


def compare(label, a_name, b_name, root):
    A, B = load(os.path.join(root, a_name)), load(os.path.join(root, b_name))
    print(label)
    pa = summarise(a_name, A); pb = summarise(b_name, B)
    if pa[1] and pb[1]:
        p = fisher(pb[0], pb[1] - pb[0], pa[0], pa[1] - pa[0])
        full = "complete set" if pa[1] == pb[1] == 12 else "INCOMPLETE set: no verdict"
        print(f"  PASS {b_name} {pb[0]}/{pb[1]} vs {a_name} {pa[0]}/{pa[1]}; Fisher two-sided p = {p:.3f} ({full})")
    print()


def main():
    root = os.path.join(sys.argv[1], "comparisons")
    compare("cmp1: previous line (A) vs new line (B), one prompt", "cmp1-A", "cmp1-B", root)
    for pr in ("P2", "P1"):
        compare(f"cmp2, prompt {pr}: line without V5 (B) vs with V5 (C); stopped early, no verdict", f"cmp2-B-{pr}", f"cmp2-C-{pr}", root)


if __name__ == "__main__":
    main()
