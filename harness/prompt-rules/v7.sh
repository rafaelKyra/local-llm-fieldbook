#!/bin/bash
# Round 7: closing-line rule (control vs p3f) on FIXED paid OpenRouter models. OR_KEY from the environment of THIS process only. Spend cap CAP_USD (default 4) read from the key before each call.
# The free tier allows 1000 requests per day (reset 00:00 UTC): runs cut off by a rate limit are moved to interrupted/ (never counted) and redone after the wait.
cd "$(dirname "$0")"; R=${REPS:-16}; W=${WINDOW:-64000}; PORT=${PORT:-8098}
MODELS=${MODELS:-"qwen/qwen3.8-27b qwen/qwen3.8-flash deepseek/deepseek-v4.1-flash-1017 openai/gpt-oss-120b qwen/qwen3.7-flash z-ai/glm-4.7-flash z-ai/glm-5.3-flash anthropic/claude-haiku-5.5 qwen/qwen3-coder-next"}
log() { echo "$(date -Is) $*" >> night7/progress.txt; }
[ -n "$OR_KEY" ] || { echo "OR_KEY not set"; exit 2; }
export FORGE_API_KEY="$OR_KEY"; unset OR_KEY; mkdir -p night7
spent() { curl -sS -m 20 https://openrouter.ai/api/v1/key -H "Authorization: Bearer $FORGE_API_KEY" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['usage'])" 2>/dev/null || echo 0; }
over() { python3 -c "import sys;sys.exit(0 if float(sys.argv[1])>=float(sys.argv[2]) else 1)" "$(spent)" "${CAP_USD:-4}"; }
wait_reset() { local now=$(date -u +%s); local next=$(( (now/86400+1)*86400 + 120 )); log "daily limit: waiting $(( (next-now)/60 )) min for the reset"; sleep $((next-now)); }
for M in $MODELS; do
  S=$(echo "$M" | tr '/:' '__'); OUT=night7/$S; mkdir -p $OUT/kits
  node or-proxy.mjs $OUT/served-models.jsonl $PORT >> $OUT/proxy.log 2>&1 & PROXY=$!; sleep 1
  k() { node kitrun.mjs --base-url http://127.0.0.1:$PORT/v1 --model "$M" --out $OUT/kits --window $W "$@" >> $OUT/kits.log 2>&1; }
  log "model $M start reps=$R"
  for pass in $(seq 1 60); do
    for r in $(seq 1 $R); do
      for kit in P3b P3c; do
        if [ $((r % 2)) -eq 1 ]; then A="control p3f"; else A="p3f control"; fi
        for arm in $A; do
          if over; then log "spend cap reached ($(spent) USD): stopping"; kill $PROXY 2>/dev/null; touch night7/DONE; exit 0; fi
          if [ "$arm" = p3f ]; then k --kits $kit --arms p3f --reps $r --lib ./lib-finish.js; else k --kits $kit --arms control --reps $r; fi
          Q=$(python3 quarantine.py $OUT); case "$Q" in *daily=1*) wait_reset ;; *moved=0*) ;; *) log "interrupted ($Q), waiting 3 min"; sleep 180 ;; esac
        done
      done
      log "model $M rep $r done"
    done
    n=$(ls $OUT/kits/P3*.json 2>/dev/null | wc -l); [ "$n" -ge $((R*4)) ] && break
    if [ "$pass" -ge 2 ] && [ "$n" -eq 0 ]; then log "model $M unusable: no run completed in two passes"; break; fi
  done
  kill $PROXY 2>/dev/null; log "model $M done ($n rows)"
done
log "round 6 all done"; touch night7/DONE
