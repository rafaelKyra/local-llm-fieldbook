#!/bin/bash
# Round 10: closing-line rule (control vs p3f), kits P3b and P3c, on three models hosted by Berget AI (EU). Paid per token (EUR). BERGET_KEY from the environment of THIS process only.
# No usage endpoint exists for this key, so spend is ESTIMATED from the token counts of every row (input at full price, no cache discount) and the run stops at CAP_EUR (default 3).
cd "$(dirname "$0")"; R=${REPS:-16}; W=${WINDOW:-64000}; U=https://api.berget.ai/v1; mkdir -p night10
MODELS=${MODELS:-"google/gemma-4-31B-it|0.25|0.5 zai-org/GLM-5.3-Flash|0.25|0.5 mistralai/Mistral-Small-3.2-24B-Instruct-2506|0.3|0.3"}
log() { echo "$(date -Is) $*" >> night10/progress.txt; }
[ -n "$BERGET_KEY" ] || { echo "BERGET_KEY not set"; exit 2; }
export FORGE_API_KEY="$BERGET_KEY"; unset BERGET_KEY
spent() { python3 - <<'PY'
import glob, json
P = {"gemma": (0.25, 0.5), "GLM": (0.25, 0.5), "Mistral": (0.3, 0.3)}
t = 0.0
for f in glob.glob("night10/*/kits/*.json") + glob.glob("night10/*/interrupted/*.json") + glob.glob("night10/*/redone-discarded/*.json"):
    try:
        u = json.load(open(f))["usage"]
    except Exception:
        continue
    k = "gemma" if "gemma" in f else "GLM" if "GLM" in f else "Mistral"
    t += (u.get("inputTokens", 0) * P[k][0] + u.get("outputTokens", 0) * P[k][1]) / 1e6
print(f"{t:.4f}")
PY
}
over() { python3 -c "import sys;sys.exit(0 if float(sys.argv[1])>=float(sys.argv[2]) else 1)" "$(spent)" "${CAP_EUR:-3}"; }
for E in $MODELS; do
  M=${E%%|*}; S=$(echo "$M" | tr '/:' '__'); OUT=night10/$S; mkdir -p $OUT/kits
  k() { node kitrun.mjs --base-url $U --model "$M" --out $OUT/kits --window $W "$@" >> $OUT/kits.log 2>&1; }
  log "model $M start reps=$R (estimated spend so far $(spent) EUR)"
  for pass in $(seq 1 6); do
    for r in $(seq 1 $R); do
      for kit in P3b P3c; do
        if [ $((r % 2)) -eq 1 ]; then A="control p3f"; else A="p3f control"; fi
        for arm in $A; do
          if over; then log "estimated spend cap reached ($(spent) EUR): stopping"; touch night10/DONE; exit 0; fi
          if [ "$arm" = p3f ]; then k --kits $kit --arms p3f --reps $r --lib ./lib-finish.js; else k --kits $kit --arms control --reps $r; fi
          Q=$(python3 quarantine.py $OUT); case "$Q" in *moved=0*) ;; *) log "interrupted ($Q), waiting 2 min"; sleep 120 ;; esac
        done
      done
      log "model $M rep $r done (estimated spend $(spent) EUR)"
    done
    n=$(ls $OUT/kits/P3*.json 2>/dev/null | wc -l); [ "$n" -ge $((R*4)) ] && break
    if [ "$pass" -ge 2 ] && [ "$n" -eq 0 ]; then log "model $M unusable: no run completed in two passes"; break; fi
  done
  log "model $M done ($n rows)"
done
log "round 10 all done (estimated spend $(spent) EUR)"; touch night10/DONE
