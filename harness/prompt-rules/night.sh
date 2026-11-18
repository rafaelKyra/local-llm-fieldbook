#!/bin/bash
# Overnight screening B (2026-11-17): the closing line (P3) and the shortcut ledger (P4) as four arms (control, p3, p4, p34), on Mercury-3 first (fast) and then on the local 27B.
#   units: (a) the two experiment kits with their hidden checks, (b) the Forge bench (30 basic + 8 spec tasks), one repetition per invocation, a different seed per repetition.
# Resumable: a unit whose result file exists is skipped, so the script can simply be started again. The Mercury key is read from FORGE_API_KEY in the environment of THIS process only; it is never written to a file,
# and it is removed from the environment before the local phase.
cd "$(dirname "$(readlink -f "$0")")" || exit 2
N=$PWD/night; mkdir -p $N; P=$N/progress.txt
LM=http://localhost:1234/v1; LMODEL=qwen3.8-27b-turbo-fable-cold-fusion-735-882-heretic-uncensored-neo-coder-max-mtp
MURL=https://api.inceptionlabs.ai/v1; MMODEL=mercury-3
ARMS=(control p3 p4 p34)
KIT_REPS_M=${KIT_REPS_M:-15}; BENCH_REPS_M=${BENCH_REPS_M:-3}; KIT_REPS_L=${KIT_REPS_L:-10}; BENCH_REPS_L=${BENCH_REPS_L:-2}
log(){ echo "$(date -Is) $*" | tee -a $P; }
policy_arg(){ [ "$1" = control ] && echo "" || echo "--policy policy-$1.json"; }
bench_unit(){ # model-dir url model window concurrency arm rep
  local d=$N/$1/bench-$6-r$7
  [ -s $d/summary.json ] && return 0
  log "bench $1 arm=$6 rep=$7 start"
  node bench/run.mjs --base-url $2 --model $3 --suite all --concurrency $5 --context-window $4 --seed-offset $7 --label $1-$6 --out $d $(policy_arg $6) > $N/$1/bench-$6-r$7.log 2>&1
  [ -s $d/summary.json ] && log "bench $1 arm=$6 rep=$7 done: $(python3 -c "import json;s=json.load(open('$d/summary.json'));print(s['solved'],'/',s['tasks'],'solved, out tokens',s['outputTokens'],', sec',s['totalSeconds'])")" || log "bench $1 arm=$6 rep=$7 FAILED (see bench-$6-r$7.log)"
}
guard_local(){ # the model must be fully on the GPU: a spill (fewer than 60 layers) costs 3x speed
  local n; n=$(ps -o args -C llama-server | grep -o -- "--n-gpu-layers [0-9]*" | head -1 | awk '{print $2}')
  if [ -z "$n" ] || [ "$n" -lt 60 ]; then
    log "WARNING: local model has n-gpu-layers=${n:-none}; reloading with all layers on the GPU"
    ~/.lmstudio/bin/lms unload "$LMODEL" >/dev/null 2>&1; sleep 4
    ~/.lmstudio/bin/lms load "$LMODEL" --gpu max --context-length 75008 --parallel 1 --identifier "$LMODEL" -y >/dev/null 2>&1; sleep 4
    n=$(ps -o args -C llama-server | grep -o -- "--n-gpu-layers [0-9]*" | head -1 | awk '{print $2}'); log "after reload n-gpu-layers=${n:-none}"
  fi
}
phase(){ # name url model window concurrency kitreps benchreps local?
  local d=$N/$1; mkdir -p $d/kits
  log "== phase $1 start (kits reps=$6, bench reps=$7)"
  [ "$8" = local ] && guard_local
  node kitrun.mjs --base-url $2 --model $3 --out $d/kits --reps $6 --window $4 >> $d/kits.log 2>&1
  log "kits $1 done: $(ls $d/kits/*.json 2>/dev/null | wc -l) rows"
  for ((r=0; r<$7; r++)); do
    for ((i=0; i<${#ARMS[@]}; i++)); do arm=${ARMS[$(( (i + r) % ${#ARMS[@]} ))]}; [ "$8" = local ] && guard_local; bench_unit $1 $2 $3 $4 $5 $arm $r; done
  done
  log "== phase $1 done"
}
log "=== night start. Mercury key present: $([ -n "$FORGE_API_KEY" ] && echo yes || echo no)"
if [ -n "$FORGE_API_KEY" ]; then phase mercury3 $MURL $MMODEL 64000 4 $KIT_REPS_M $BENCH_REPS_M remote; fi
unset FORGE_API_KEY
phase local27b $LM $LMODEL 70000 1 $KIT_REPS_L $BENCH_REPS_L local
python3 summarize.py $N > $N/RESULT-tables.md 2>&1
log "=== night done; tables in night/RESULT-tables.md"
echo done > $N/DONE
