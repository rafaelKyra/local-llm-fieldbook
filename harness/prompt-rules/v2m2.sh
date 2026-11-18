#!/bin/bash
cd "$(dirname "$0")"; OUT=night2/mercury3; U=https://api.inceptionlabs.ai/v1; MD=mercury-3; R=${REPS:-30}
echo "$(date -Is) mercury P4b-v2 lanes start" >> night2/progress.txt
( node kitrun.mjs --base-url $U --model $MD --out $OUT/kits --reps $R --window 90112 --kits P4b --arms control,p4 >> $OUT/kits-d.log 2>&1 ) &
( node kitrun.mjs --base-url $U --model $MD --out $OUT/kits --reps $R --window 90112 --kits P4b --arms p4f --lib ./lib-finish-p4.js >> $OUT/kits-e.log 2>&1 ) &
wait; echo "$(date -Is) mercury P4b-v2 done" >> night2/progress.txt; touch night2/MERCURY2-DONE
