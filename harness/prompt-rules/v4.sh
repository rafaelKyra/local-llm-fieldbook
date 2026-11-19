#!/bin/bash
# Round 4: OxCoder 9B i1 MTP Q4_K_S (LM Studio, MTP draft, ctx 75008) as the weaker model. Kits P3b and P3c (control, p3, p3f; 20 reps), then the 38-task bench (control vs p3f, REPS reps).
cd "$(dirname "$0")"; OUT=night4/oxcoder; mkdir -p $OUT/kits
U=http://127.0.0.1:1234/v1; MD=oxcoder-9b-mtp; R=${REPS:-20}; BR=${BREPS:-2}; W=75008
log() { echo "$(date -Is) $*" >> night4/progress.txt; }
k() { node kitrun.mjs --base-url $U --model $MD --out $OUT/kits --reps $R --window $W "$@" >> $OUT/kits.log 2>&1; }
log "oxcoder kits start reps=$R"
k --kits P3b,P3c --arms control,p3
k --kits P3b,P3c --arms p3f --lib ./lib-finish.js
log "oxcoder kits done"
b() { [ -s $OUT/bench-$1-r$3/summary.json ] && return; log "bench oxcoder arm=$1 rep=$3 start"
  node $2/run.mjs --base-url $U --model $MD --suite all --concurrency 1 --context-window 64000 --seed-offset $3 --label oxcoder-$1 --out $OUT/bench-$1-r$3 > $OUT/bench-$1-r$3.log 2>&1
  [ -s $OUT/bench-$1-r$3/summary.json ] && log "bench oxcoder arm=$1 rep=$3 done: $(python3 -c "import json;s=json.load(open('$OUT/bench-$1-r$3/summary.json'));print(s['solved'],'/',s['tasks'],'solved, out tokens',s['outputTokens'],', sec',s['totalSeconds'])")" || log "bench oxcoder arm=$1 rep=$3 FAILED"; }
for r in $(seq 0 $((BR-1))); do b control bench $r; b p3f bench-pf $r; done
log "oxcoder all done"; touch night4/OX-DONE
