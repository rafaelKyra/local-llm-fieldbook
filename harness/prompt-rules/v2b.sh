#!/bin/bash
# Full Forge bench (30 basic + 8 spec tasks) on Mercury-3 with the closing line placed in the finish tool (patched lib, arm p3f), 3 repetitions with the same seeds as the control rows of night/mercury3 (bench-control-r0..r2).
cd "$(dirname "$0")"; OUT=night2/mercury3; mkdir -p $OUT
for r in 0 1 2; do
  echo "$(date -Is) bench mercury3 arm=p3f rep=$r start" >> night2/progress.txt
  node bench-pf/run.mjs --base-url https://api.inceptionlabs.ai/v1 --model mercury-3 --suite all --concurrency 4 --context-window 64000 --seed-offset $r --label mercury3-p3f --out $OUT/bench-p3f-r$r > $OUT/bench-p3f-r$r.log 2>&1
  [ -s $OUT/bench-p3f-r$r/summary.json ] && echo "$(date -Is) bench mercury3 arm=p3f rep=$r done: $(python3 -c "import json;s=json.load(open('$OUT/bench-p3f-r$r/summary.json'));print(s['solved'],'/',s['tasks'],'solved, out tokens',s['outputTokens'],', sec',s['totalSeconds'])")" >> night2/progress.txt || echo "$(date -Is) bench mercury3 arm=p3f rep=$r FAILED" >> night2/progress.txt
done
touch night2/BENCHF-DONE
