#!/bin/bash
# Round 3: second closing-line kit (P3c) on Strata, 20 reps, arms control / p3 (system prompt) / p3f (finish tool description). No key needed.
cd "$(dirname "$0")"; OUT=night3/strata; mkdir -p $OUT/kits
U=http://127.0.0.1:8080/v1; MD=qwen3.8-flash-next-iq3_s; R=${REPS:-20}; W=90112
log() { echo "$(date -Is) $*" >> night3/progress.txt; }
k() { node kitrun.mjs --base-url $U --model $MD --out $OUT/kits --reps $R --window $W "$@" >> $OUT/kits.log 2>&1; }
log "strata P3c start reps=$R"
k --kits P3c --arms control,p3
k --kits P3c --arms p3f --lib ./lib-finish.js
log "strata P3c done"; touch night3/P3C-DONE
