#!/usr/bin/env node
// Logging pass-through proxy to OpenRouter for the router model "openrouter/free" (which serves a different free model per request).
// Records, per request: time, HTTP status, the model and provider that actually answered, and token usage. It never logs headers, prompts or the key:
// the client's Authorization header is forwarded as is. usage: node or-proxy.mjs LOGFILE [PORT]
import http from 'http';
import { appendFileSync } from 'fs';
const log = process.argv[2]; const port = Number(process.argv[3] ?? 8099);
if (!log) { console.error('usage: node or-proxy.mjs LOGFILE [PORT]'); process.exit(64); }
const UP = 'https://openrouter.ai/api/v1';
http.createServer(async (req, res) => {
  const chunks = []; for await (const c of req) chunks.push(c);
  const body = Buffer.concat(chunks); const t0 = Date.now();
  let status = 0; let text = '';
  try {
    const r = await fetch(UP + req.url.replace(/^\/v1/, ''), { method: req.method, headers: { 'content-type': req.headers['content-type'] ?? 'application/json', authorization: req.headers.authorization ?? '', accept: req.headers.accept ?? '*/*' }, body: req.method === 'GET' ? undefined : body });
    status = r.status;
    const h = { 'content-type': r.headers.get('content-type') ?? 'application/json' };
    res.writeHead(status, h);
    const reader = r.body.getReader();
    for (;;) { const { done, value } = await reader.read(); if (done) break; res.write(value); if (text.length < 400000) text += Buffer.from(value).toString('utf8'); }
    res.end();
  } catch (e) { if (!res.headersSent) res.writeHead(502); res.end(String(e)); text = text || String(e); status = status || 502; }
  let model = null, provider = null, pt = null, ct = null, err = null;
  const m = text.match(/"model"\s*:\s*"([^"]+)"/); if (m) model = m[1];
  const p = text.match(/"provider"\s*:\s*"([^"]+)"/); if (p) provider = p[1];
  const u1 = text.match(/"prompt_tokens"\s*:\s*(\d+)/g); const u2 = text.match(/"completion_tokens"\s*:\s*(\d+)/g);
  if (u1) pt = Number(u1[u1.length - 1].match(/\d+/)[0]); if (u2) ct = Number(u2[u2.length - 1].match(/\d+/)[0]);
  if (status >= 400) err = text.slice(0, 160).replace(/sk-or-[A-Za-z0-9-]+/g, '[key]');
  appendFileSync(log, JSON.stringify({ t: t0, ms: Date.now() - t0, status, model, provider, pt, ct, err }) + '\n');
}).listen(port, '127.0.0.1', () => console.log('proxy on', port));
