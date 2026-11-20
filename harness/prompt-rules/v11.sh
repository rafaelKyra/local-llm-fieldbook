#!/bin/bash
# Round 11 (plan: AUDIT-PACK-2026-11-19/PREREG-round11-mercury.md, written before any run). Mercury 3 (Inception API, direct), SYNTHETIC kits and bench only; no private code.
# Part A: kits P3b+P3c, control vs p3f, 32 reps per kit and arm. Part B: 38-task bench, control vs p3f, 4 passes each, alternating.
# INC_KEY from the environment of THIS process only. Spend is ESTIMATED from token counts at list price (0.20 in / 0.70 out USD per M, no cache discount) and the run stops at CAP_USD (default 3).
cd "$(dirname "$0")"; R=${REPS:-32}; BR=${BENCH_REPS:-4}; W=64000; U=https://api.inceptionlabs.ai/v1; M=mercury-3; OUT=night11/mercury-3; mkdir -p $OUT/kits
log() { echo "$(date -Is) $*" >> night11/progress.txt; }
[ -n "$INC_KEY" ] || { echo "INC_KEY not set"; exit 2; }
export FORGE_API_KEY="$INC_KEY"; unset INC_KEY
spent() { python3 - <<'PY'
import glob, json
t = 0.0
for f in glob.glob("night11/mercury-3/kits/*.json") + glob.glob("night11/mercury-3/interrupted/*.json"):
    try: u = json.load(open(f))["usage"]
    except Exception: continue
    t += (u.get("inputTokens", 0) * 0.20 + u.get("outputTokens", 0) * 0.70) / 1e6
for f in glob.glob("night11/mercury-3/bench-*/summary.json"):
    try: s = json.load(open(f))
    except Exception: continue
    t += (s.get("inputTokens", 0) * 0.20 + s.get("outputTokens", 0) * 0.70) / 1e6
print(f"{t:.4f}")
PY
}
over() { python3 -c "import sys;sys.exit(0 if float(sys.argv[1])>=float(sys.argv[2]) else 1)" "$(spent)" "${CAP_USD:-3}"; }
k() { node kitrun.mjs --base-url $U --model $M --out $OUT/kits --window $W "$@" >> $OUT/kits.log 2>&1; }
log "Part A start: kits, reps=$R (estimated spend $(spent) USD)"
for pass in $(seq 1 6); do
  for r in $(seq 1 $R); do
    for kit in P3b P3c; do
      if [ $((r % 2)) -eq 1 ]; then A="control p3f"; else A="p3f control"; fi
      for arm in $A; do
        if over; then log "estimated spend cap reached ($(spent) USD): stopping"; touch night11/DONE; exit 0; fi
        if [ "$arm" = p3f ]; then k --kits $kit --arms p3f --reps $r --lib ./lib-finish.js; else k --kits $kit --arms control --reps $r; fi
        Q=$(python3 quarantine.py $OUT); case "$Q" in *moved=0*) ;; *) log "interrupted ($Q), waiting 2 min"; sleep 120 ;; esac
      done
    done
    [ $((r % 4)) -eq 0 ] && log "kits rep $r done (estimated spend $(spent) USD)"
  done
  n=$(ls $OUT/kits/P3*.json 2>/dev/null | wc -l); [ "$n" -ge $((R*4)) ] && break
  if [ "$pass" -ge 2 ] && [ "$n" -eq 0 ]; then log "unusable: no run completed in two passes"; exit 1; fi
done
log "Part A done ($n rows; estimated spend $(spent) USD); Part B start: bench"
b() { # arm dir rep
  [ -s $OUT/bench-$1-r$3/summary.json ] && return
  if over; then log "estimated spend cap reached ($(spent) USD): stopping"; touch night11/DONE; exit 0; fi
  log "bench mercury arm=$1 rep=$3 start"
  node $2/run.mjs --base-url $U --model $M --suite all --concurrency 1 --context-window $W --seed-offset $3 --label mercury-$1 --out $OUT/bench-$1-r$3 > $OUT/bench-$1-r$3.log 2>&1
  [ -s $OUT/bench-$1-r$3/summary.json ] && log "bench mercury arm=$1 rep=$3 done: $(python3 -c "import json;s=json.load(open('$OUT/bench-$1-r$3/summary.json'));print(s['solved'],'/',s['tasks'],'solved, out',s['outputTokens'],', in',s['inputTokens'],', sec',round(s['totalSeconds']))") (estimated spend $(spent) USD)" || log "bench mercury arm=$1 rep=$3 FAILED (no summary)"
}
for r in $(seq 0 $((BR-1))); do
  if [ $((r % 2)) -eq 0 ]; then b control bench $r; b p3f bench-pf $r; else b p3f bench-pf $r; b control bench $r; fi
done
log "round 11 done (estimated spend $(spent) USD)"; touch night11/DONE
