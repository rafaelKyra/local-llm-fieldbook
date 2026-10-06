#!/usr/bin/env python3
"""Recomputes the per-version table of the arm iterations from the sanitised data.

Usage: arm_iterations.py <data-dir>        (the folder that holds arm-iterations/, new-models/ and replication/)

The version folders are not run1/run2/..., so analyze.py cannot read them; this script uses the same verdict function.
v1 is the earlier data under the same settings: new-models/base27-run*, new-models/gsq-run* and replication/cellB-run*
(there is none for cyber-tiel under these exact settings).
"""
import glob, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("analyze", os.path.join(HERE, "analyze.py"))
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)

SYM = {"PASS": "P", "PARTIAL": "~", "FAIL": "x", "INFRA": "-"}
MODELS = [("base27", "qwen3.8-27b"), ("gsq", "qwen3.8-27b-gsq-rco"),
          ("cyber", "cyber-tiel-coder-35b-a3b-apex-i-nanoplus"), ("holo4", "holo4-35b-a3b-i1")]
V1 = {"base27": "new-models/base27-run*", "gsq": "new-models/gsq-run*", "holo4": "replication/cellB-run*"}
VERSIONS = [("v2", "v2-first-fixes-with-regression"), ("v3", "v3-corrected"), ("v4", "v4-final"), ("v5", "v5-latest-outputs"),
            ("v6", "v6-closing-after-refusals"), ("v7", "v7-replan-gate-facts"), ("v8", "v8-verifier-whole-task"), ("v9", "v9-audit-corrections")]


def load(files):
    return [json.load(open(f)) for f in sorted(files)]


def main():
    root = sys.argv[1]
    print("%-42s %s" % ("model", "  ".join("%-6s" % v for v in ["v1"] + [v for v, _ in VERSIONS])))
    totals = {v: [0, 0, 0] for v in ["v1"] + [v for v, _ in VERSIONS]}  # runs, pass, wrote into the project
    for tag, model in MODELS:
        cells = []
        runs = load(glob.glob(os.path.join(root, V1[tag], f"{model}.json"))) if tag in V1 else []
        sets = [("v1", runs)]
        for v, folder in VERSIONS:
            sets.append((v, load(glob.glob(os.path.join(root, "arm-iterations", folder, f"{tag}-run*", f"{model}.json")))))
        for v, rs in sets:
            cells.append("%-6s" % ("".join(SYM[analyze.verdict(d)] for d in rs) or "n/a"))
            totals[v][0] += len(rs)
            totals[v][1] += sum(analyze.verdict(d) == "PASS" for d in rs)
            totals[v][2] += sum(1 for d in rs if not d.get("readOnlyKept", True))
        print("%-42s %s" % (model[:42], "  ".join(cells)))
    print()
    print("%-42s %s" % ("PASS / runs", "  ".join("%-6s" % ("%d/%d" % (totals[v][1], totals[v][0])) for v in totals)))
    print("%-42s %s" % ("runs that wrote into the project", "  ".join("%-6s" % totals[v][2] for v in totals)))


if __name__ == "__main__":
    main()
