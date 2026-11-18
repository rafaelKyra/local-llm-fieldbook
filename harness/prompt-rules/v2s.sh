#!/bin/bash
# Round 2 kits on Strata (Qwen3.8-Flash-Next IQ3_S, MTP draft, ~70-84 t/s). Sequential: Strata serves one stream well. No key needed.
cd "$(dirname "$0")"; OUT=night2/strata; mkdir -p $OUT/kits
U=http://127.0.0.1:8080/v1; MD=qwen3.8-flash-next-iq3_s; R=${REPS:-20}; W=90112
log() { echo "$(date -Is) $*" >> night2/progress.txt; }
k() { node kitrun.mjs --base-url $U --model $MD --out $OUT/kits --reps $R --window $W "$@" >> $OUT/kits.log 2>&1; }
log "strata kits start reps=$R"
k --kits P3b --arms control,p3
k --kits P3b --arms p3f --lib ./lib-finish.js
k --kits P4b --arms control,p4
k --kits P4b --arms p4f --lib ./lib-finish-p4.js
python3 summarize.py night2 > night2/RESULT-tables.md 2>&1
log "strata kits done"; touch night2/STRATA-DONE
