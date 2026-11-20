#!/usr/bin/env python3
"""Move kit rows that were cut off by the endpoint (status interrupted: rate-limited or unavailable) or crashed (status budget/unverified/blocked are real outcomes and stay) out of the result folder, so they are re-run later
instead of being counted as failures. Prints: moved=<n> daily=<0|1> (daily=1 when the proxy log shows the key's daily limit). usage: quarantine.py OUT"""
import glob, json, os, shutil, sys
out = sys.argv[1]; kits = os.path.join(out, 'kits'); qd = os.path.join(out, 'interrupted'); os.makedirs(qd, exist_ok=True)
moved = 0
for f in sorted(glob.glob(os.path.join(kits, '*.json'))):
    r = json.load(open(f))
    if r.get('status') == 'interrupted' or r.get('crash'):  # FIX 2026-11-20: only runs cut off by the endpoint (or that crashed); 'unverified', 'budget' and 'blocked' are REAL outcomes of the agent and must stay counted
        key = f"{r['kit']}.{r['arm']}.{r['rep']}"
        shutil.move(f, os.path.join(qd, os.path.basename(f)))
        d = os.path.join(kits, 'runs', key)
        if os.path.isdir(d): shutil.move(d, os.path.join(qd, 'runs-' + key + '-' + str(len(os.listdir(qd)))))
        moved += 1
daily = 0
log = os.path.join(out, 'served-models.jsonl')
if os.path.exists(log):
    for l in open(log).read().splitlines()[-30:]:
        try:
            if 'per-day' in (json.loads(l).get('err') or ''): daily = 1
        except Exception: pass
# FIX 2026-11-20: old 429 lines stay in the last 30 lines of the log after the reset; a run that completed (moved=0) must not trigger another 24 h wait
if moved == 0: daily = 0
print(f'moved={moved} daily={daily}')
