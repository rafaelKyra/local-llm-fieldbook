#!/usr/bin/env node
// Runs the two experiment kits (P3 closing line, P4 shortcut + debt ledger) against any OpenAI-compatible endpoint, four arms each (control, p3, p4, p34), real Forge core (lib.js = vendor/rafa-forge at eff27).
// The hidden check (kits/<kit>/check.py) runs only AFTER the agent has finished. The key, if any, comes from FORGE_API_KEY. Resumable: a finished (kit, arm, rep) row is skipped.
// usage: node kitrun.mjs --base-url URL --model ID --out DIR [--reps 5] [--arms control,p3,p4,p34] [--kits P3,P4,P3b,P4b] [--lib ./lib.js] [--window 90112]
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, readdirSync, statSync, existsSync, cpSync } from 'fs';
import { tmpdir } from 'os';
import * as path from 'path';
import { spawnSync } from 'child_process';

const args = process.argv.slice(2);
const libFile = (() => { const i = args.indexOf('--lib'); return i >= 0 ? args[i + 1] : './lib.js'; })();
const { runForge, FsWorkspace, NativeTools, SpawnVerifier, OpenAICompatibleModel, FsCheckDiscovery } = await import(new URL(libFile, import.meta.url).href);
const flag = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const baseUrl = flag('base-url'); const model = flag('model'); const out = flag('out');
if (!baseUrl || !model || !out) { console.error('usage: node kitrun.mjs --base-url URL --model ID --out DIR [--reps 5] [--arms ...] [--kits ...] [--window N]'); process.exit(64); }
const reps = Number(flag('reps', '5')); const window = Number(flag('window', '90112'));
const arms = flag('arms', 'control,p3,p4,p34').split(','); const kits = flag('kits', 'P3,P4').split(',');
const apiKey = process.env.FORGE_API_KEY || undefined;
const here = path.dirname(new URL(import.meta.url).pathname);
const POLICY = (arm) => (arm === 'control' || arm === 'p3f' || arm === 'p4f') ? undefined : JSON.parse(readFileSync(path.join(here, `policy-${arm}.json`), 'utf8'));
mkdirSync(path.join(out, 'runs'), { recursive: true });

const filesOf = (dir, rel = '', acc = {}) => { for (const n of readdirSync(path.join(dir, rel)).sort()) { const r = path.join(rel, n); if (n === '__pycache__') continue; const st = statSync(path.join(dir, r)); if (st.isDirectory()) filesOf(dir, r, acc); else acc[r] = readFileSync(path.join(dir, r), 'utf8'); } return acc; };

async function runOne(kit, arm, rep) {
  const key = `${kit}.${arm}.${rep}`; const rowFile = path.join(out, `${key}.json`);
  if (existsSync(rowFile)) return JSON.parse(readFileSync(rowFile, 'utf8'));
  const kitDir = path.join(here, 'kits', kit);
  const request = readFileSync(path.join(kitDir, 'TASK.md'), 'utf8');
  const root = mkdtempSync(path.join(tmpdir(), `kit-${kit}-`));
  for (const [rel, content] of Object.entries(filesOf(path.join(kitDir, 'fixture')))) { mkdirSync(path.dirname(path.join(root, rel)), { recursive: true }); writeFileSync(path.join(root, rel), content); }
  const started = Date.now(); let result; let crash = null;
  try {
    result = await runForge({
      runId: key, request, model: new OpenAICompatibleModel({ baseUrl, model, apiKey, timeoutMs: 900_000 }),
      tools: new NativeTools(root), workspace: new FsWorkspace(root), verifier: new SpawnVerifier(root, 60_000), verifyCommand: 'python3 -m unittest discover -s .',
      profile: 'auto', contextWindow: window, maxToolCalls: 40, policy: POLICY(arm), discovery: new FsCheckDiscovery(root), seed: rep, temperature: undefined, extraProtectedPaths: ['test_*.py'],
    });
  } catch (e) { crash = String(e); }
  const seconds = (Date.now() - started) / 1000;
  const runDir = path.join(out, 'runs', key); mkdirSync(runDir, { recursive: true });
  cpSync(root, path.join(runDir, 'project'), { recursive: true, filter: (s) => !s.includes('__pycache__') });
  const reply = result?.finalMessage ?? '';
  writeFileSync(path.join(runDir, 'reply.txt'), reply);
  const chk = spawnSync('python3', ['-I', path.join(kitDir, 'check.py'), path.join(runDir, 'reply.txt')], { encoding: 'utf8', timeout: 180_000 });
  const lines = (chk.stdout ?? '').split('\n');
  const flagOf = (name) => lines.some((l) => l.startsWith(`PASS ${name}`));
  const cost = (lines.find((l) => l.startsWith('COST ')) ?? '').match(/reply-chars=(\d+) added-lines=(\d+)/);
  const row = {
    kit, arm, rep, seconds, solved: flagOf('SOLVED'), behaviour: flagOf('BEHAVIOUR'), replyChars: cost ? Number(cost[1]) : null, addedLines: cost ? Number(cost[2]) : null,
    replyShortcut: lines.some((l) => l.startsWith('NOTE_REPLY_SHORTCUT=True')),
    status: result?.status, stopReason: result?.stopReason, usage: result?.usage, crash, checkExit: chk.status,
    evidence: lines.filter((l) => l.startsWith('  tail:') || l.startsWith('  comment:') || l.startsWith('  info:')).join('\n'),
  };
  writeFileSync(rowFile, JSON.stringify(row, null, 1));
  rmSync(root, { recursive: true, force: true });
  console.log(`${key}: solved=${row.solved} behaviour=${row.behaviour} (${seconds.toFixed(0)} s, calls ${row.usage?.modelCalls}, out ${row.usage?.outputTokens}${crash ? ', CRASH ' + crash.slice(0, 80) : ''})`);
  return row;
}

for (let rep = 1; rep <= reps; rep++) {
  for (const [ki, kit] of kits.entries()) {
    const order = arms.map((_, i) => arms[(i + rep + ki) % arms.length]);   // the order of the arms rotates between repetitions and kits
    for (const arm of order) await runOne(kit, arm, rep);
  }
}
console.log('kitrun done');
