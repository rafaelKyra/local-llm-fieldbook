#!/usr/bin/env python3
"""Build the blinded audit sheet from the plan in AUDIT-PACK-2026-11-19/PLAN-truthfulness-audit.md. Writes audit-items.md (no arm shown) and audit-key.json (id -> run) and copies the replies."""
import glob, hashlib, json, os, random, shutil
S = "/home/h/SafeKeeping/778/rafa-harvest-fixes-2026-11-17/screen-B"; OUT = os.path.dirname(os.path.abspath(__file__))
MODELS = [("mistral", f"{S}/night10/mistralai_Mistral-Small-3.2-24B-Instruct-2506", ("P3b", "P3c")), ("deepseek", f"{S}/night7/deepseek_deepseek-v4.1-flash-1017", ("P3b", "P3c")), ("strata", f"{S}/night3/strata", ("P3c",))]
pool = []
for name, d, kits in MODELS:
    for arm in ("control", "p3f"):
        rows = []
        for f in glob.glob(f"{d}/kits/P3*.{arm}.*.json"):
            j = json.load(open(f))
            if j["kit"] in kits and j.get("status") != "interrupted" and j["behaviour"]:
                key = f"{j['kit']}.{arm}.{j['rep']}"; rp = f"{d}/kits/runs/{key}/reply.txt"
                if os.path.exists(rp): rows.append((hashlib.sha256(f"{name}/{key}".encode()).hexdigest(), name, key, j, rp))
        pool += sorted(rows)[:12]
random.seed(20261120); random.shuffle(pool)
key = {}; md = ["# Blinded audit sheet (arm hidden). Label each id S / V / F / K per PLAN-truthfulness-audit.md\n"]
os.makedirs(f"{OUT}/replies", exist_ok=True)
for i, (h, name, rk, j, rp) in enumerate(pool, 1):
    iid = f"A{i:03d}"; key[iid] = {"model": name, "run": rk, "arm": j["arm"], "kit": j["kit"], "solved": j["solved"]}
    shutil.copy(rp, f"{OUT}/replies/{iid}-{name}-{rk}.txt")
    lines = [l.strip() for l in open(rp, encoding="utf-8").read().splitlines() if l.strip()][-8:]
    info = [l for l in j.get("evidence", "").splitlines() if "info:" in l]
    md.append(f"## {iid} | {j['kit']} | {name} | {info[0].strip() if info else ''}")
    MARK = ("real export", "real file", "real data", "no real", "actual export", "actual file", "sample file", "vendor's file", "not tested", "untested", "did not test", "didn't test", "not verified", "unverified", "could not verify", "couldn't verify", "cannot verify", "can't verify", "did not verify", "didn't verify", "not checked", "did not check", "didn't check", "assum", "ambigu", "caveat", "risk", "not covered", "limitation", "haven't", "have not")
    for k, l in enumerate(lines):
        full = (len(lines) - k <= 5) or any(m in l.lower() for m in MARK)
        md.append("> " + (l[:900] if full else l[:120] + (" ..." if len(l) > 120 else "")))
    md.append("")
open(f"{OUT}/audit-items.md", "w").write("\n".join(md)); json.dump(key, open(f"{OUT}/audit-key.json", "w"), indent=1)
import collections; print(len(pool), "items;", dict(collections.Counter((v["model"], v["arm"]) for v in key.values())))
