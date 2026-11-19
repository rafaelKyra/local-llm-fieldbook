#!/bin/bash
# Full Forge bench (38 tasks) on Strata, control (bench/run.mjs) vs p3f (bench-pf/run.mjs), alternating, REPS repetitions, concurrency 1, window 64000.
cd "$(dirname "$0")"; OUT=night3/strata; mkdir -p $OUT; R=${REPS:-2}
U=http://127.0.0.1:8080/v1; MD=qwen3.8-flash-next-iq3_s
log() { echo "$(date -Is) $*" >> night3/progress.txt; }
b() { # arm dir rep
  [ -s $OUT/bench-$1-r$3/summary.json ] && return
  log "bench strata arm=$1 rep=$3 start"
  node $2/run.mjs --base-url $U --model $MD --suite all --concurrency 1 --context-window 64000 --seed-offset $3 --label strata-$1 --out $OUT/bench-$1-r$3 > $OUT/bench-$1-r$3.log 2>&1
  [ -s $OUT/bench-$1-r$3/summary.json ] && log "bench strata arm=$1 rep=$3 done: $(python3 -c "import json;s=json.load(open('$OUT/bench-$1-r$3/summary.json'));print(s['solved'],'/',s['tasks'],'solved, out tokens',s['outputTokens'],', sec',s['totalSeconds'])")" || log "bench strata arm=$1 rep=$3 FAILED"
}
for r in $(seq 0 $((R-1))); do b control bench $r; b p3f bench-pf $r; done
log "bench strata done"; touch night3/BENCH-DONE
