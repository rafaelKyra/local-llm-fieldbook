#!/bin/bash
# Round 5: closing-line rule (control vs p3f) on the OpenRouter router model "openrouter/free" (a different free model may answer each request).
# The key comes from OR_KEY in the environment of THIS process only; it is not written to any file. A logging proxy records which model answered each request.
# Arms are INTERLEAVED (same repetition, both arms, alternating order) so that router drift hits both equally. Resumable (kitrun skips finished rows).
cd "$(dirname "$0")"; OUT=night5/openrouter; mkdir -p $OUT/kits
R=${REPS:-20}; W=${WINDOW:-64000}; PORT=8099
log() { echo "$(date -Is) $*" >> night5/progress.txt; }
[ -n "$OR_KEY" ] || { echo "OR_KEY not set"; exit 2; }
node or-proxy.mjs $OUT/served-models.jsonl $PORT >> $OUT/proxy.log 2>&1 &
PROXY=$!; trap 'kill $PROXY 2>/dev/null' EXIT; sleep 1
export FORGE_API_KEY="$OR_KEY"; unset OR_KEY
k() { node kitrun.mjs --base-url http://127.0.0.1:$PORT/v1 --model openrouter/free --out $OUT/kits --window $W "$@" >> $OUT/kits.log 2>&1; }
log "openrouter start reps=$R"
for r in $(seq 1 $R); do
  for kit in ${KITS:-P3b P3c}; do
    if [ $((r % 2)) -eq 1 ]; then A="control p3f"; else A="p3f control"; fi
    for arm in $A; do
      if [ "$arm" = p3f ]; then k --kits $kit --arms p3f --reps $r --lib ./lib-finish.js; else k --kits $kit --arms control --reps $r; fi
    done
  done
  log "openrouter rep $r done"
done
log "openrouter all done"; touch night5/OR-DONE
