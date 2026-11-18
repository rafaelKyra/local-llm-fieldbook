#!/bin/bash
# Round 2 on Mercury-3 (fast, hosted): the same kits and arms, 30 repetitions each, three parallel lanes. FORGE_API_KEY comes from the environment of this process only.
cd "$(dirname "$0")"; OUT=night2/mercury3; mkdir -p $OUT/kits
U=https://api.inceptionlabs.ai/v1; MD=mercury-3; R=${REPS:-30}
log() { echo "$(date -Is) $*" >> night2/progress.txt; }
log "mercury lanes start reps=$R"
( node kitrun.mjs --base-url $U --model $MD --out $OUT/kits --reps $R --window 90112 --kits P3b --arms control,p3 >> $OUT/kits-a.log 2>&1 ) &
( node kitrun.mjs --base-url $U --model $MD --out $OUT/kits --reps $R --window 90112 --kits P3b --arms p3f --lib ./lib-finish.js >> $OUT/kits-b.log 2>&1 ) &
( node kitrun.mjs --base-url $U --model $MD --out $OUT/kits --reps $R --window 90112 --kits P4b --arms control,p4 >> $OUT/kits-c.log 2>&1 ) &
wait
log "mercury lanes done"; touch night2/MERCURY-DONE
