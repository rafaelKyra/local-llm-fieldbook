#!/usr/bin/env node
// Stage 2 of the PUBLIC bench: validate candidates by running the project's own tests (vitest) in temp exports. Touches nothing in the clones.
//  (a) parent tree + the fix's test files overlaid must FAIL on real assertions, twice (a suite that cannot load is not counted as a failure);
//  (b) the fix tree must PASS those test files, twice.
// Records failure messages so a missing-symbol failure ("is not a function", "is not defined", "does not provide an export") can be filtered later as unfair.
// usage: node validate_public.mjs IN.jsonl OUT.jsonl CLONES_ROOT [--per-repo N] [--workers K]
import { spawn, spawnSync } from 'child_process';
import { mkdtempSync, symlinkSync, mkdirSync, writeFileSync, readFileSync, rmSync, existsSync, appendFileSync } from 'fs';
import { tmpdir } from 'os';
import * as path from 'path';
const args = process.argv.slice(2); const [inF, outF, root] = args;
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? Number(args[i + 1]) : d; };
const perRepo = opt('per-repo', 14), workers = opt('workers', 3);
const repos = new Set(['fb55/htmlparser2', 'felladrin/MiniSearch', 'dyoshikawa/rulesync', 'nansen-ai/nansen-cli', 'agentclientprotocol/claude-agent-acp', 'solidjs/solid-router']);
const all = readFileSync(inF, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l)).filter((c) => repos.has(c.repo));
// deterministic sample: smallest sources first is biased, so order by a hash of the sha
const h = (s) => [...s].reduce((a, ch) => (a * 31 + ch.charCodeAt(0)) >>> 0, 7);
const byRepo = {}; for (const c of all) (byRepo[c.repo] ||= []).push(c);
const cands = Object.values(byRepo).flatMap((v) => v.sort((a, b) => h(a.sha) - h(b.sha)).slice(0, perRepo));
writeFileSync(outF, '');
const sh = (cmd, cwd) => spawnSync('sh', ['-c', cmd], { cwd, encoding: 'utf8', timeout: 120000, maxBuffer: 256 * 1024 * 1024 });
function runOnce(c, ref, overlay) {
  const R = path.join(root, path.basename(c.repo)); const tmp = mkdtempSync(path.join(tmpdir(), 'pb-'));
  return new Promise((resolve) => {
    const done = (v) => { rmSync(tmp, { recursive: true, force: true }); resolve(v); };
    if (sh(`git -C '${R}' archive ${ref} | tar -x -C '${tmp}'`).status !== 0) return done({ err: 'export' });
    if (existsSync(path.join(R, 'node_modules'))) symlinkSync(path.join(R, 'node_modules'), path.join(tmp, 'node_modules'));
    if (overlay) for (const f of c.tests) { const b = sh(`git -C '${R}' show ${c.sha}:'${f}'`); if (b.status !== 0) return done({ err: 'overlay ' + f }); mkdirSync(path.dirname(path.join(tmp, f)), { recursive: true }); writeFileSync(path.join(tmp, f), b.stdout); }
    const out = path.join(tmp, '.res.json');
    const p = spawn(path.join(R, 'node_modules/.bin/vitest'), ['run', ...c.tests, '--reporter=json', `--outputFile=${out}`], { cwd: tmp, stdio: 'ignore' });
    const t = setTimeout(() => p.kill('SIGKILL'), 240000);
    p.on('close', (code) => {
      clearTimeout(t); let j = null; try { j = JSON.parse(readFileSync(out, 'utf8')); } catch { /* no result */ }
      if (!j) return done({ code, err: 'no-json' });
      const tests = j.testResults.flatMap((x) => x.assertionResults);
      done({ code, passed: tests.filter((x) => x.status === 'passed').length, failed: tests.filter((x) => x.status === 'failed').length, loadFail: j.testResults.filter((x) => x.status === 'failed' && x.assertionResults.length === 0).length,
        failedNames: tests.filter((x) => x.status === 'failed').map((x) => x.fullName).slice(0, 8), msgs: tests.filter((x) => x.status === 'failed').flatMap((x) => x.failureMessages).map((m) => m.split('\n')[0].slice(0, 200)).slice(0, 6) });
    });
  });
}
async function validate(c) {
  const rec = { ...c, valid: false };
  const a1 = await runOnce(c, c.parent, true); rec.parentRun1 = a1;
  if (a1.err || !(a1.failed > 0)) { rec.reason = 'parent+tests does not fail on assertions'; return rec; }
  const f1 = await runOnce(c, c.sha, false); rec.fixRun1 = f1;
  if (f1.err || f1.failed > 0 || !(f1.passed > 0)) { rec.reason = 'fix does not pass'; return rec; }
  const a2 = await runOnce(c, c.parent, true), f2 = await runOnce(c, c.sha, false); rec.parentRun2 = a2; rec.fixRun2 = f2;
  if (a2.err || !(a2.failed > 0) || a2.failed !== a1.failed || f2.err || f2.failed > 0 || f2.passed !== f1.passed) { rec.reason = 'unstable between two runs'; return rec; }
  rec.valid = true; return rec;
}
let i = 0, n = 0; const t0 = Date.now();
await Promise.all(Array.from({ length: workers }, async () => { while (i < cands.length) { const c = cands[i++]; const r = await validate(c); appendFileSync(outF, JSON.stringify(r) + '\n'); n++; console.log(`${n}/${cands.length} ${r.valid ? 'VALID ' : 'reject'} ${c.repo}@${c.sha.slice(0, 7)} ${r.valid ? '' : r.reason} (${Math.round((Date.now() - t0) / 1000)} s)`); } }));
console.log('done');
