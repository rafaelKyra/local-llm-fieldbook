#!/usr/bin/env python3
"""Analysis of the live-orchestration ruler. Usage: analyze.py <data-dir> [--json out.json]

<data-dir> holds run1/, run2/, ... each with one <model>.json per model (sanitised).
Per model, over the runs it has:
  PASS      final report holds all four facts, the project was not touched, the plan was not abandoned and the session ended on its own
            (a step that failed and was recovered still counts, see the deviation log; the facts are matched by regular expressions:
            the test total must appear as the literal 74 and 'none' anywhere stands for 'no file changed', so the check can accept
            or reject a report a person would judge differently)
  PARTIAL   same, but at least two (not four) facts
  FAIL      anything else (did not finish, endpoint error, timed out, touched the project, fewer than two facts)
  INFRA     did not load: excluded from rates (reported separately)
Primary statistic: PASS rate over all runs, Wilson 95% interval (same formula as harness/score_grid.py).
Sensitivity: PASS rate over runs 2..n only (run 1 was seen before the protocol was registered).
Bands: models sorted by PASS rate; a model joins the current band while its interval overlaps the band leader's.
Models in one band are not ranked against each other. With three runs the intervals are wide: expect few bands.
"""
import glob, json, math, os, statistics, sys


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


V1_FACTS = ("mentionsJavac", "mentionsTests74", "mentionsApkSize", "claimsNoChanges")
V2_FACTS = ("mentionsJavac", "testsFactV2", "mentionsApkSize", "claimsNoChanges")
V3_FACTS = ("mentionsJavac", "testsFactV3", "mentionsApkSize", "claimsNoChanges")


def verdict(d, scorer=1):
    """scorer 1 = the published instrument (literal 74). scorer 2 = the test fact also accepts the four per-class counts; it exists
    only for runs that record `testsFactV2` (a change of instrument, fixed before use, never applied to older runs).
    scorer 3 (from 2026-10-07) takes the expected test counts from the project's own result files at the START of each run (stored in the
    run as `expectedTests`), because the project gained a test and v1 (literal 74) and v2 (four fixed classes) then failed correct reports."""
    if d.get("loadFailed"):
        return "INFRA"
    checks = d.get("reportChecks") or {}
    if scorer == 3 and "testsFactV3" in checks:
        keys = V3_FACTS
    else:
        keys = V2_FACTS if scorer == 2 and "testsFactV2" in checks else V1_FACTS
    facts = sum(1 for k in keys if checks.get(k))
    # A plan that was abandoned is not a session that ended on its own (the harness' own `finished` says so too).
    # A step that failed and was recovered still counts: that was decided in the deviation log of PROTOCOL.md.
    if d.get("upstreamError") or d.get("timedOut") or d.get("threw") or d.get("noResult") or d.get("planAbandoned"):
        return "FAIL"
    if not d.get("readOnlyKept", False):
        return "FAIL"
    if facts == 4:
        return "PASS"
    return "PARTIAL" if facts >= 2 else "FAIL"


def load(data_dir):
    runs = {}
    for run_dir in sorted(glob.glob(os.path.join(data_dir, "run*"))):
        n = int(os.path.basename(run_dir)[3:])
        for p in glob.glob(os.path.join(run_dir, "*.json")):
            d = json.load(open(p))
            if "model" in d:
                runs.setdefault(d["model"], {})[n] = d
    return runs


def main():
    data_dir = sys.argv[1]
    out_json = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    rows = []
    for model, by_run in load(data_dir).items():
        vs = {n: verdict(d) for n, d in by_run.items()}
        scored = {n: v for n, v in vs.items() if v != "INFRA"}
        n = len(scored)
        k = sum(1 for v in scored.values() if v == "PASS")
        later = [v for r, v in scored.items() if r >= 2]
        done = [d for r, d in by_run.items() if vs[r] in ("PASS", "PARTIAL")]
        lo, hi = wilson(k, n)
        rows.append({
            "model": model, "runs": n, "verdicts": [vs[r] for r in sorted(vs)],
            "pass": k, "pass_rate": (k / n) if n else None, "ci95": [round(lo, 3), round(hi, 3)],
            "pass_rate_runs_2plus": (sum(1 for v in later if v == "PASS") / len(later)) if later else None,
            "median_seconds_when_finished": statistics.median([d["elapsedSeconds"] for d in done]) if done else None,
            "median_tokens_when_finished": statistics.median([d["stepTokens"] for d in done]) if done else None,
            "median_tool_calls_when_finished": statistics.median([d["toolCalls"] for d in done]) if done else None,
            "repeatable": len(set(scored.values())) <= 1 if n >= 2 else None,
            "loadedContext": next((d.get("loadedContext") for d in by_run.values() if d.get("loadedContext")), None),
            "vramMiB": next((d.get("vramMiBAfterLoad") for d in by_run.values() if d.get("vramMiBAfterLoad")), None),
        })
    rows.sort(key=lambda r: (-(r["pass_rate"] or 0), -r["runs"], r["median_seconds_when_finished"] or 10**9))
    band, leader = 0, None
    for r in rows:
        if r["runs"] == 0:
            r["band"] = None
            continue
        if leader is None or r["ci95"][1] < leader["ci95"][0]:
            band, leader = band + 1, r
        r["band"] = band
    print("%-4s %-50s %-3s %-12s %-14s %-9s %-7s %-7s" % ("band", "model", "n", "verdicts", "PASS rate 95%CI", "median s", "tokens", "repeat"))
    for r in rows:
        print("%-4s %-50s %-3s %-12s %-14s %-9s %-7s %-7s" % (
            r["band"], r["model"][:50], r["runs"], "/".join({"PASS": "P", "PARTIAL": "~", "FAIL": "x", "INFRA": "-"}[v] for v in r["verdicts"]),
            "%d/%d [%.2f-%.2f]" % (r["pass"], r["runs"], r["ci95"][0], r["ci95"][1]) if r["runs"] else "-",
            r["median_seconds_when_finished"], r["median_tokens_when_finished"],
            {True: "yes", False: "no", None: "n=1"}[r["repeatable"]]))
    inf = [m for m, d in load(data_dir).items() if all(verdict(x) == "INFRA" for x in d.values())]
    if inf:
        print("\nINFRA (did not load, excluded):", ", ".join(inf))
    if out_json:
        json.dump(rows, open(out_json, "w"), indent=1)


if __name__ == "__main__":
    main()
