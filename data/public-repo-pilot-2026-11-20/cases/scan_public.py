#!/usr/bin/env python3
"""Stage 1 of the PUBLIC real-repository bench: metadata only (GitHub API via gh, read-only, nothing cloned).
Finds fix commits made on or after SINCE in public TypeScript/JavaScript repositories that use vitest, change tests and 1-3 source files (<=150 changed lines).
SINCE is chosen after the training cutoff of the models under test as far as it is known (best effort; see README).
usage: scan_public.py SINCE OUT.jsonl"""
import json, re, subprocess, sys, base64, collections
SINCE, OUT = sys.argv[1], sys.argv[2]
def gh(*a):
    r = subprocess.run(['gh', 'api', *a], capture_output=True, text=True)
    if r.returncode: return None
    try: return json.loads(r.stdout)
    except Exception: return None
repos = {}
queries = ['language:TypeScript stars:100..20000 pushed:>%s size:<60000 archived:false fork:false license:mit' % SINCE,
           'language:TypeScript stars:100..20000 pushed:>%s size:<60000 archived:false fork:false license:apache-2.0' % SINCE,
           'language:JavaScript stars:100..20000 pushed:>%s size:<60000 archived:false fork:false license:mit' % SINCE]
for q in queries:
    for page in (1, 2, 3):
        d = gh('-X', 'GET', 'search/repositories', '-f', 'q=' + q, '-f', 'sort=updated', '-f', 'per_page=50', '-f', f'page={page}')
        for it in (d or {}).get('items', []): repos[it['full_name']] = it
print('repos found', len(repos), file=sys.stderr)
TEST = re.compile(r'(^|/)(tests?|__tests__|spec|specs)/|(\.|_)(test|spec)\.[a-z]+$', re.I)
CODE = re.compile(r'\.(ts|tsx|js|jsx|mjs|cjs)$', re.I)
out = open(OUT, 'w'); stats = collections.Counter()
for name, it in sorted(repos.items()):
    pj = gh(f'repos/{name}/contents/package.json')
    if not pj or 'content' not in pj: stats['no package.json'] += 1; continue
    try: p = json.loads(base64.b64decode(pj['content']))
    except Exception: stats['bad package.json'] += 1; continue
    deps = {**p.get('devDependencies', {}), **p.get('dependencies', {})}
    if 'vitest' not in deps: stats['no vitest'] += 1; continue
    stats['vitest repos'] += 1
    cs = gh(f'repos/{name}/commits', '-X', 'GET', '-f', f'since={SINCE}T00:00:00Z', '-f', 'per_page=100') or []
    for c in cs:
        m = c['commit']['message'].split('\n')[0]
        if not re.match(r'^(fix|bug)(\(|:|!)', m, re.I) or len(c.get('parents', [])) != 1: continue
        d = gh(f'repos/{name}/commits/{c["sha"]}')
        if not d: continue
        fs = d.get('files', [])
        t = [f['filename'] for f in fs if TEST.search(f['filename']) and f['status'] != 'removed']
        s = [f for f in fs if CODE.search(f['filename']) and not TEST.search(f['filename'])]
        lines = sum(f['additions'] + f['deletions'] for f in s)
        if not t or not (1 <= len(s) <= 3) or lines > 150 or len(fs) > 8: stats['commit filtered'] += 1; continue
        stats['candidate commits'] += 1
        out.write(json.dumps({'repo': name, 'sha': c['sha'], 'parent': c['parents'][0]['sha'], 'date': c['commit']['committer']['date'], 'subject_HINT_only': m,
                              'tests': t, 'src': [f['filename'] for f in s], 'src_lines': lines, 'size_kb': it['size'], 'stars': it['stargazers_count'], 'license': (it.get('license') or {}).get('spdx_id')}) + '\n')
out.close(); print(dict(stats), file=sys.stderr)
