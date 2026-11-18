#!/usr/bin/env python3
"""Tables of a screening-B result folder. usage: summarize.py <night-dir>. Reads kit rows (<model>/kits/*.json) and bench summaries (<model>/bench-<arm>-r<N>/summary.json)."""
import json, glob, os, sys, statistics as st
root = sys.argv[1]
def mean(xs): xs = [x for x in xs if x is not None]; return (sum(xs) / len(xs)) if xs else float('nan')
for mdir in sorted(d for d in glob.glob(os.path.join(root, '*')) if os.path.isdir(d)):
    name = os.path.basename(mdir)
    rows = [json.load(open(f)) for f in glob.glob(os.path.join(mdir, 'kits', '*.json'))]
    if rows:
        print(f'\n## {name}: experiment kits ({len(rows)} runs)')
        print('| kit | arm | runs | solved | behaviour (of solved) | out tokens | calls | seconds | reply chars | crashes |')
        print('|---|---|---|---|---|---|---|---|---|---|')
        for kit in sorted({r['kit'] for r in rows}):
            for arm in ['control', 'p3', 'p3f', 'p4', 'p4f', 'p34']:
                rs = [r for r in rows if r['kit'] == kit and r['arm'] == arm]
                if not rs: continue
                sol = [r for r in rs if r['solved']]
                print(f"| {kit} | {arm} | {len(rs)} | {len(sol)}/{len(rs)} | {sum(r['behaviour'] for r in sol)}/{len(sol)}, reply-note {sum(1 for r in rs if r.get('replyShortcut'))} | {mean([ (r.get('usage') or {}).get('outputTokens') for r in rs]):.0f} | {mean([(r.get('usage') or {}).get('modelCalls') for r in rs]):.1f} | {mean([r['seconds'] for r in rs]):.0f} | {mean([r['replyChars'] for r in rs]):.0f} | {sum(1 for r in rs if r.get('crash'))} |")
    bsum = {}
    for f in glob.glob(os.path.join(mdir, 'bench-*', 'summary.json')):
        arm = os.path.basename(os.path.dirname(f)).split('-')[1]; s = json.load(open(f)); a = bsum.setdefault(arm, {'tasks': 0, 'solved': 0, 'out': 0, 'inp': 0, 'sec': 0.0, 'calls': 0, 'runs': 0})
        a['tasks'] += s['tasks']; a['solved'] += s['solved']; a['out'] += s['outputTokens']; a['inp'] += s['inputTokens']; a['sec'] += s['totalSeconds']; a['calls'] += s['toolCalls']; a['runs'] += 1
    if bsum:
        print(f'\n## {name}: bench (basic + spec tasks, summed over repetitions)')
        print('| arm | task runs | solved | rate | output tokens | input tokens | tool calls | seconds |')
        print('|---|---|---|---|---|---|---|---|')
        for arm in ['control', 'p3', 'p3f', 'p4', 'p4f', 'p34']:
            a = bsum.get(arm)
            if a: print(f"| {arm} | {a['tasks']} | {a['solved']} | {a['solved']/a['tasks']:.3f} | {a['out']} | {a['inp']} | {a['calls']} | {a['sec']:.0f} |")
