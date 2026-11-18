#!/bin/bash
# Screening B, round 2: kits where the behaviour is warranted (P3b, P4b) + the closing line placed in the finish tool (p3f). Local 27B only unless FORGE_API_KEY is set for Mercury (then a second pass).
cd "$(dirname "$0")"
OUT=night2; mkdir -p $OUT
log() { echo "$(date -Is) $*" >> $OUT/progress.txt; }
run() { # name base model window reps
  d=$OUT/$1; mkdir -p $d/kits
  log "kits $1 P3b control,p3 start"; node kitrun.mjs --base-url $2 --model $3 --out $d/kits --reps $5 --window $4 --kits P3b --arms control,p3 >> $d/kits.log 2>&1
  log "kits $1 P3b p3f start"; node kitrun.mjs --base-url $2 --model $3 --out $d/kits --reps $5 --window $4 --kits P3b --arms p3f --lib ./lib-finish.js >> $d/kits.log 2>&1
  log "kits $1 P4b control,p4 start"; node kitrun.mjs --base-url $2 --model $3 --out $d/kits --reps $5 --window $4 --kits P4b --arms control,p4 >> $d/kits.log 2>&1
  log "kits $1 done"
}
run local27b http://localhost:1234/v1 qwen3.8-27b-turbo-fable-cold-fusion-735-882-heretic-uncensored-neo-coder-max-mtp 70000 10
if [ -n "$FORGE_API_KEY" ]; then run mercury3 https://api.inceptionlabs.ai/v1 mercury-3 90112 15; fi
python3 summarize.py $OUT > $OUT/RESULT-tables.md 2>&1
log "done"; touch $OUT/DONE
