#!/usr/bin/env python3
"""Aggregate table for the real-repository pilot. usage: pilot_table.py data/real-repo-pilot-2026-11-20  (reads <model>/bench-<arm>-r<N>.summary.json; standard library only)
The 20 cases are private (taken from the author's repositories); only the per-pass summaries are published, never case names or contents."""
import glob, json, os, sys
d = sys.argv[1]
print("| model | pass | solved | verdicts | output tokens | tool calls | seconds |\n|---|---|---|---|---|---|---|")
for f in sorted(glob.glob(os.path.join(d, "*", "*.summary.json"))):
    s = json.load(open(f)); m = os.path.basename(os.path.dirname(f)); n = os.path.basename(f).replace(".summary.json", "")
    v = ", ".join(f"{k} {c}" for k, c in sorted(s["verdicts"].items(), key=lambda x: -x[1]))
    print(f"| {m} | {n} | {s['solved']}/{s['tasks']} | {v} | {s['outputTokens']} | {s['toolCalls']} | {s['totalSeconds']:.0f} |")
