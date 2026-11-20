#!/bin/bash
# Round 9: 38-task synthetic bench, control vs p3f, on deepseek/deepseek-v4.1-flash-1017 via OpenRouter (paid). Cost-only question: the bench is at its ceiling (38/38) for capable models.
# OR_KEY from the environment of THIS process only (never written to a file). Stops when the key's total usage reaches CAP_USD (default 4.0; key limit 5).
cd "$(dirname "$0")"; R=${REPS:-8}; M=deepseek/deepseek-v4.1-flash-1017; OUT=night9/deepseek-v4.1-flash-1017; mkdir -p $OUT
log() { echo "$(date -Is) $*" >> night9/progress.txt; }
[ -n "$OR_KEY" ] || { echo "OR_KEY not set"; exit 2; }
export FORGE_API_KEY="$OR_KEY"; unset OR_KEY
spent() { curl -sS -m 20 https://openrouter.ai/api/v1/key -H "Authorization: Bearer $FORGE_API_KEY" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['usage'])" 2>/dev/null || echo 0; }
over() { python3 -c "import sys;sys.exit(0 if float(sys.argv[1])>=float(sys.argv[2]) else 1)" "$(spent)" "${CAP_USD:-4.0}"; }
b() { # arm dir rep
  [ -s $OUT/bench-$1-r$3/summary.json ] && return
  if over; then log "spend cap reached ($(spent) USD): stopping"; exit 0; fi
  log "bench deepseek arm=$1 rep=$3 start"
  node $2/run.mjs --base-url https://openrouter.ai/api/v1 --model $M --suite all --concurrency 1 --context-window 64000 --seed-offset $3 --label deepseek-$1 --out $OUT/bench-$1-r$3 > $OUT/bench-$1-r$3.log 2>&1
  [ -s $OUT/bench-$1-r$3/summary.json ] && log "bench deepseek arm=$1 rep=$3 done: $(python3 -c "import json;s=json.load(open('$OUT/bench-$1-r$3/summary.json'));print(s['solved'],'/',s['tasks'],'solved, out tokens',s['outputTokens'],', in',s['inputTokens'],', sec',round(s['totalSeconds']))")" || log "bench deepseek arm=$1 rep=$3 FAILED (no summary)"
}
for r in $(seq 0 $((R-1))); do
  if [ $((r % 2)) -eq 0 ]; then b control bench $r; b p3f bench-pf $r; else b p3f bench-pf $r; b control bench $r; fi
done
log "round 9 done; key usage $(spent) USD"; touch night9/DONE
