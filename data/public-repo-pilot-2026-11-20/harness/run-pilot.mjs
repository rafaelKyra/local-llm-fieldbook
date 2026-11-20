#!/usr/bin/env node
// Copy of ../bench-pf/run.mjs for the real-repository pilot (suite 'pilot') with the Forge library chosen by --lib (default ../dist/lib.js = control; ../dist-finish/lib.js = p3f).
// Runs the benchmark tasks against any OpenAI-compatible endpoint. The key, if needed, is read from FORGE_API_KEY.
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync } from 'fs';
import { tmpdir } from 'os';
import * as path from 'path';
import { createHash } from 'crypto';
import { spawnSync, spawn } from 'child_process';
import { TASKS } from '../bench-pf/tasks.mjs';
import { SPEC_TASKS } from '../bench-pf/tasks-spec.mjs';
import { REAL_TASKS } from '../bench-pf/tasks-real.mjs';
import { symlinkSync } from 'fs';
import { PILOT_TASKS } from './tasks-pilot.mjs';
import { PUBLIC_TASKS } from './tasks-public.mjs';
const LIB = (() => { const i = process.argv.indexOf('--lib'); return new URL(i >= 0 ? process.argv[i + 1] : '../dist/lib.js', import.meta.url).href; })();
const { runForge, FsWorkspace, NativeTools, SpawnVerifier, OpenAICompatibleModel, runArgv } = await import(LIB);

const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const baseUrl = flag('base-url'); const model = flag('model');
if (!baseUrl || !model) { console.error('usage: node bench/run.mjs --base-url URL --model ID [--concurrency 4] [--profile auto] [--tasks a,b] [--context-window N] [--max-tool-calls N] [--out DIR] [--label NAME]'); process.exit(64); }
const runtime = flag('runtime', 'forge'); // forge | pi
const PI_BIN = flag('pi-bin', path.resolve('..', 'rafa-ai', 'node_modules', '.bin', 'pi'));
const concurrency = Number(flag('concurrency', '4'));
const only = flag('tasks') ? new Set(flag('tasks').split(',')) : null;
const profile = flag('profile', 'auto');
const contextWindow = Number(flag('context-window', '32768'));
const maxToolCalls = Number(flag('max-tool-calls', '40'));
const repeat = Number(flag('repeat', '1'));
const seedOffset = Number(flag('seed-offset', '0')); // screening B: one repetition per invocation, a different seed for each
const temperature = flag('temperature') ? Number(flag('temperature')) : undefined;
const label = flag('label', model.replace(/[^\w.-]+/g, '_'));
const out = flag('out', path.join('bench', 'results', `${label}-${new Date().toISOString().replace(/[:.]/g, '-')}`));
mkdirSync(out, { recursive: true });
// --lab-cases FILE: use Harness Lab's case files (git repos at a defective commit, external checks, no check given to the agent).
const labCases = flag('lab-cases') ? JSON.parse(readFileSync(flag('lab-cases'), 'utf8')).map((c) => ({
  id: c.id, category: c.family ?? 'lab', request: c.request, lab: { repo: c.repo.replace('/media/veracrypt2/', '/media/veracrypt1/'), ref: c.base_ref, checks: c.checks },
})) : null;
const policy = flag('policy') ? JSON.parse(readFileSync(flag('policy'), 'utf8')) : undefined;
const apiKey = process.env.FORGE_API_KEY || undefined;
const sha = (s) => createHash('sha256').update(s).digest('hex');

// Runs the pi coding agent (non-interactive, JSON events) on the same workspace and request; counts executed tools and tokens from its events.
async function runPi(task, root, timeoutMs = 20 * 60 * 1000) {
  const agentDir = mkdtempSync(path.join(tmpdir(), 'pi-agent-'));
  writeFileSync(path.join(agentDir, 'models.json'), JSON.stringify({ providers: { bench: { baseUrl, api: 'openai-completions', apiKey: apiKey || 'local', compat: { supportsDeveloperRole: false, supportsReasoningEffort: false }, models: [{ id: model }] } } }), { mode: 0o600 });
  const message = (task.lab || task.git) ? task.request : `${task.request}\n\nThe project check is: ${task.verify} (run it to verify your work before you finish).`;
  const usage = { turns: 0, toolCalls: 0, inputTokens: 0, outputTokens: 0 };
  let status = 'completed';
  await new Promise((resolve) => {
    const child = spawn(PI_BIN, ['-p', '--mode', 'json', '--no-session', '--provider', 'bench', '--model', model, message], { cwd: root, env: { ...process.env, PI_CODING_AGENT_DIR: agentDir }, stdio: ['ignore', 'pipe', 'pipe'] });
    const timer = setTimeout(() => { status = 'budget'; child.kill('SIGKILL'); }, timeoutMs);
    let buf = '';
    child.stdout.on('data', (b) => {
      buf += b.toString('utf8');
      let i;
      while ((i = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, i); buf = buf.slice(i + 1);
        try {
          const e = JSON.parse(line);
          if (e.type === 'tool_execution_start') usage.toolCalls++;
          if (e.type === 'turn_end') { usage.turns++; usage.inputTokens += e.message?.usage?.input ?? 0; usage.outputTokens += e.message?.usage?.output ?? 0; }
        } catch { /* not an event line */ }
      }
    });
    child.on('close', (code) => { clearTimeout(timer); if (code !== 0 && status === 'completed') status = 'error'; resolve(); });
  });
  rmSync(agentDir, { recursive: true, force: true });
  return { status, usage };
}

async function runTask(task, rep) {
  const root = mkdtempSync(path.join(tmpdir(), `bench-${task.id}-`));
  if (task.git) {
    // export only the paths that exist in the parent commit (a path missing there, e.g. tsconfig.node.json in rafa-forge, made the whole run crash)
    const have = [...new Set(task.git.paths)].filter((pth) => spawnSync('git', ['-C', task.git.repo, 'cat-file', '-e', `${task.git.fix}^:${pth}`]).status === 0);
    const x = spawnSync('sh', ['-c', `git -C '${task.git.repo}' archive ${task.git.fix}^ ${have.join(' ')} | tar -x -C '${root}'`]);
    if (x.status !== 0) throw new Error(`cannot export ${task.id}: ${x.stderr}`);
    symlinkSync(path.join(task.git.repo, 'node_modules'), path.join(root, 'node_modules'));
  }
  if (task.lab) {
    const tar = spawnSync('sh', ['-c', `git -C '${task.lab.repo}' archive ${task.lab.ref} | tar -x -C '${root}'`]);
    if (tar.status !== 0) throw new Error(`cannot export ${task.lab.repo}: ${tar.stderr}`);
  }
  for (const [rel, content] of Object.entries(task.files ?? {})) { mkdirSync(path.dirname(path.join(root, rel)), { recursive: true }); writeFileSync(path.join(root, rel), content); }
  const checkFile = (task.lab || task.git) ? null : task.verify.includes('check.py') ? 'check.py' : 'check.js';
  const checkHash = checkFile ? sha(task.files[checkFile]) : '';
  const started = Date.now();
  let result; let crash = null;
  try {
    if (runtime === 'pi') {
      const r = await runPi(task, root);
      let fresh = false;
      if (!task.lab && !task.git) fresh = (await runArgv(root, task.verify, 60_000)).status === 'pass';
      result = { status: r.status, stopReason: r.status, finalMessage: '', profile: 'pi', bundle: { hash: 'pi' }, usage: r.usage, pathologies: {}, integrity: {}, verification: { fresh } };
    } else
    result = await runForge({
      runId: `${task.id}-${rep}`, request: task.request,
      model: new OpenAICompatibleModel({ baseUrl, model, apiKey, timeoutMs: 900_000 }),
      tools: new NativeTools(root), workspace: new FsWorkspace(root), verifier: new SpawnVerifier(root, 60_000),
      verifyCommand: (task.lab || task.git) ? undefined : task.verify, profile, contextWindow, maxToolCalls, policy, seed: rep + seedOffset, temperature, extraProtectedPaths: checkFile ? [checkFile] : [],
    });
  } catch (e) { crash = String(e); }
  const seconds = (Date.now() - started) / 1000;
  let hidden = null; let tampered = false;
  try {
    if (task.git) {
      for (const f of task.git.testFiles) {
        const body = spawnSync('git', ['-C', task.git.repo, 'show', `${task.git.fix}:${f}`], { encoding: 'utf8' });
        mkdirSync(path.dirname(path.join(root, f)), { recursive: true }); writeFileSync(path.join(root, f), body.stdout);
      }
      hidden = spawnSync(task.hiddenArgv[0], task.hiddenArgv.slice(1), { cwd: root, timeout: 180_000 }).status === 0;
    } else if (task.lab) {
      hidden = task.lab.checks.every((c) => spawnSync(c.argv[0], c.argv.slice(1), { cwd: root, timeout: 60_000 }).status === 0);
    } else {
      tampered = sha(readFileSync(path.join(root, checkFile), 'utf8')) !== checkHash;
      for (const [rel, content] of Object.entries(task.hidden)) writeFileSync(path.join(root, rel), content);
      hidden = (await runArgv(root, task.hiddenCommand, 60_000)).status === 'pass';
    }
  } catch (e) { crash = crash ?? String(e); }
  const visible = result?.verification.fresh ?? false;
  const verdict = tampered ? 'tampered' : hidden ? 'solved' : visible ? 'overfit' : crash ? 'crash' : result?.status === 'blocked' ? 'blocked' : result?.status === 'budget' ? 'budget' : 'failed';
  return { id: task.id, category: task.category, rep, verdict, visible, hidden, seconds, crash, status: result?.status, stopReason: result?.stopReason, profile: result?.profile, usage: result?.usage, pathologies: result?.pathologies, integrity: result?.integrity, bundle: result?.bundle?.hash, finalMessage: result?.finalMessage?.slice(0, 400), root };
}

const suite = flag('suite', 'basic');
const pool = labCases ?? (suite === 'public' ? PUBLIC_TASKS : suite === 'pilot' ? PILOT_TASKS : suite === 'real' ? REAL_TASKS : suite === 'spec' ? SPEC_TASKS : suite === 'all' ? [...TASKS, ...SPEC_TASKS] : TASKS);
const jobs = pool.filter((t) => !only || only.has(t.id)).flatMap((t) => Array.from({ length: repeat }, (_, r) => [t, r]));
const results = []; let next = 0;
await Promise.all(Array.from({ length: Math.min(concurrency, jobs.length) }, async () => {
  while (next < jobs.length) {
    const [t, r] = jobs[next++];
    const prev = path.join(out, `${t.id}.${r}.json`);
    if (existsSync(prev)) { const res = JSON.parse(readFileSync(prev, 'utf8')); results.push(res); console.log(`${res.verdict.padEnd(9)} ${t.id.padEnd(18)} (kept from an earlier pass of this run)`); continue; }
    let res;
    try { res = await runTask(t, r); } catch (e) { res = { id: t.id, category: t.category, rep: r, verdict: 'harness_error', visible: false, hidden: null, seconds: 0, crash: String(e).slice(0, 300) }; }
    results.push(res);
    console.log(`${res.verdict.padEnd(9)} ${t.id.padEnd(18)} ${res.seconds.toFixed(1).padStart(6)}s  tools ${res.usage?.toolCalls ?? '-'}  ${Object.keys(res.pathologies ?? {}).join(',')}`);
    writeFileSync(path.join(out, `${t.id}.${r}.json`), JSON.stringify(res, null, 2));
  }
}));

const by = (f) => results.reduce((m, r) => (m[f(r)] = (m[f(r)] ?? 0) + 1, m), {});
const solved = results.filter((r) => r.verdict === 'solved').length;
const sum = (k) => results.reduce((a, r) => a + (r.usage?.[k] ?? 0), 0);
const wilson = (k, n) => { if (!n) return [0, 0]; const z = 1.96, p = k / n, d = 1 + z * z / n, c = p + z * z / (2 * n), m = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [+((c - m) / d).toFixed(3), +((c + m) / d).toFixed(3)]; };
const perTask = results.reduce((m, r) => ((m[r.id] ??= []).push(r.verdict === 'solved'), m), {});
const passAtK = Object.values(perTask).filter((v) => v.some(Boolean)).length;
const passPowK = Object.values(perTask).filter((v) => v.every(Boolean)).length;
const summary = {
  passAtK: `${passAtK}/${Object.keys(perTask).length}`, passPowK: `${passPowK}/${Object.keys(perTask).length}`, wilson95: wilson(solved, results.length),
  label, model, profile, runtime, tasks: results.length, solved, rate: +(solved / results.length).toFixed(3), verdicts: by((r) => r.verdict),
  byCategory: Object.fromEntries(Object.entries(results.reduce((m, r) => ((m[r.category] ??= []).push(r.verdict === 'solved' ? 1 : 0), m), {})).map(([k, v]) => [k, `${v.reduce((a, b) => a + b, 0)}/${v.length}`])),
  totalSeconds: +results.reduce((a, r) => a + r.seconds, 0).toFixed(1), toolCalls: sum('toolCalls'), inputTokens: sum('inputTokens'), outputTokens: sum('outputTokens'),
  pathologies: results.reduce((m, r) => { for (const [k, v] of Object.entries(r.pathologies ?? {})) m[k] = (m[k] ?? 0) + v; return m; }, {}),
};
writeFileSync(path.join(out, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('\n' + JSON.stringify(summary, null, 2));
