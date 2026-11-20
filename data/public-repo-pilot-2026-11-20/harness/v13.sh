#!/bin/bash
# Round 13 (plan: AUDIT-PACK-2026-11-19/PREREG-round13-public-pilot.md, written before any run). Public real-repository pilot, Mercury 3, control vs p3f, 2 passes each.
# INC_KEY from the environment of THIS process only. Spend ESTIMATED from token counts at list price (0.20 in / 0.70 out USD per M, no cache discount); stops at CAP_USD (default 10).
cd "$(dirname "$0")"; PASSES=${PASSES:-2}; M=mercury-3; U=https://api.inceptionlabs.ai/v1; OUT=night13/mercury-3; mkdir -p $OUT
log() { echo "$(date -Is) $*" >> night13/progress.txt; }
[ -n "$INC_KEY" ] || { echo "INC_KEY not set"; exit 2; }
export FORGE_API_KEY="$INC_KEY"; unset INC_KEY
spent() { python3 - <<'PY'
import glob, json
t = 0.0
for f in glob.glob("night13/mercury-3/bench-*/*.json"):
    if f.endswith("summary.json"): continue
    try: u = json.load(open(f))["usage"]
    except Exception: continue
    if isinstance(u, dict): t += (u.get("inputTokens", 0) * 0.20 + u.get("outputTokens", 0) * 0.70) / 1e6
print(f"{t:.4f}")
PY
}
over() { python3 -c "import sys;sys.exit(0 if float(sys.argv[1])>=float(sys.argv[2]) else 1)" "$(spent)" "${CAP_USD:-10}"; }
pass() { # arm lib rep
  [ -s $OUT/bench-$1-r$3/summary.json ] && return
  if over; then log "estimated spend cap reached ($(spent) USD): stopping"; touch night13/DONE; exit 0; fi
  log "pilot mercury arm=$1 pass=$3 start (estimated spend $(spent) USD)"
  node real-bench/run-pilot.mjs --suite public --base-url $U --model $M --lib $2 --context-window 64000 --max-tool-calls 60 --concurrency 1 --profile auto --seed-offset $3 --out $OUT/bench-$1-r$3 > $OUT/bench-$1-r$3.log 2>&1
  [ -s $OUT/bench-$1-r$3/summary.json ] && log "pilot mercury arm=$1 pass=$3 done: $(python3 -c "import json;s=json.load(open('$OUT/bench-$1-r$3/summary.json'));print(s['solved'],'/',s['tasks'],'solved, out',s['outputTokens'],', in',s['inputTokens'],', sec',round(s['totalSeconds']),s['verdicts'])") (estimated spend $(spent) USD)" || log "pilot mercury arm=$1 pass=$3 FAILED (no summary)"
}
for r in $(seq 0 $((PASSES-1))); do
  if [ $((r % 2)) -eq 0 ]; then pass control ../dist/lib.js $r; pass p3f ../dist-finish/lib.js $r; else pass p3f ../dist-finish/lib.js $r; pass control ../dist/lib.js $r; fi
done
log "round 13 done (estimated spend $(spent) USD)"; touch night13/DONE
