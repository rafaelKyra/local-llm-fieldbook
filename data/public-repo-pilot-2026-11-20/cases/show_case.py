#!/usr/bin/env python3
"""Show what is needed to write a symptom report for one case: failing assertions on the parent and the ADDED lines of the fix's test files (the commit message is NOT shown). usage: show_case.py SHA_PREFIX..."""
import json,subprocess,sys,os
R='/home/h/SafeKeeping/778/public-bench-repos'
rows={json.loads(l)['sha'][:8]:json.loads(l) for l in open('validated-stage2.jsonl')}
for p in sys.argv[1:]:
    r=rows[p[:8]]; repo=os.path.join(R,os.path.basename(r['repo']))
    print('='*100); print(r['repo'],r['sha'][:8],'src',r['src'])
    print('FAIL msgs:',' || '.join(m[:170] for m in r['parentRun1']['msgs'][:3]))
    for t in r['tests']:
        d=subprocess.run(['git','-C',repo,'diff','-U2',r['parent'],r['sha'],'--',t],capture_output=True,text=True).stdout
        lines=[l for l in d.split('\n') if not l.startswith(('diff','index','---','+++'))]
        print('--- test diff',t); print('\n'.join(l[:150] for l in lines[:70]))
