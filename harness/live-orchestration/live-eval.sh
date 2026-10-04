#!/usr/bin/env bash
# One model at a time through a live orchestration arm; everything unloaded between; load settings pinned.
#
#   ARM_RUN=/path/to/arm-run.sh PROJECT=<dir> OUT=<dir> ./live-eval.sh <model-key> [<model-key> ...]
#
# ARM_RUN is the arm's own command for ONE run. It is called as
#     $ARM_RUN <model-key> <context-length> <out-dir> <prompt-file> <pristine-dir> <project-dir>
# and must leave <out-dir>/<model-key with / replaced by _>.json behind. The arm itself is not in this repository.
# ORDER_SEED=<int> shuffles the model list deterministically (default: keep the given order).
# Per model: the largest context of 100000 / 80000 / 65000 that loads with --gpu max, else automatic offload
# (recorded as "65000-auto-offload"). --parallel 1 always. lms --estimate-only is not used: it ignores the context.
set -u
OUT=${OUT:?folder prepared with prepare.sh}
PROJECT=${PROJECT:?project dir}
ARM_RUN=${ARM_RUN:?the arm command}
PRISTINE=${PRISTINE:-"$OUT/pristine"}
mkdir -p "$OUT/logs"
models=("$@")
if [ -n "${ORDER_SEED:-}" ]; then
  mapfile -t models < <(python3 - "$ORDER_SEED" "${models[@]}" <<'PY'
import random,sys
seed,*m=sys.argv[1:]
random.Random(int(seed)).shuffle(m)
print("\n".join(m))
PY
)
fi
for m in "${models[@]}"; do
  safe=$(echo "$m" | tr '/' '_')
  echo "[$(date +%H:%M:%S)] START $m"
  lms unload --all >/dev/null 2>&1; sleep 2
  loaded=""; t0=$(date +%s)
  for ctx in 100000 80000 65000; do
    if timeout -k 10 420 lms load "$m" --gpu max -c "$ctx" --parallel 1 -y >"$OUT/logs/$safe.load.log" 2>&1; then loaded="$ctx"; break; fi
    lms unload --all >/dev/null 2>&1
  done
  if [ -z "$loaded" ] && timeout -k 10 420 lms load "$m" -c 65000 --parallel 1 -y >>"$OUT/logs/$safe.load.log" 2>&1; then
    loaded="65000-auto-offload"
  fi
  if [ -z "$loaded" ]; then
    echo "[$(date +%H:%M:%S)] LOADFAIL $m"
    python3 -c "import json,sys; json.dump({'model':sys.argv[1],'loadFailed':True}, open(sys.argv[2],'w'), indent=1)" "$m" "$OUT/$safe.json"
    continue
  fi
  loadsecs=$(( $(date +%s) - t0 ))
  vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1)
  "$ARM_RUN" "$m" "${loaded%%-*}" "$OUT" "$OUT/prompt.txt" "$PRISTINE" "$PROJECT"
  rc=$?
  python3 - "$OUT/$safe.json" "$loaded" "$vram" "$loadsecs" "$rc" <<'PY'
import json,os,sys
p,ctx,vram,secs,rc=sys.argv[1:6]
d=json.load(open(p)) if os.path.exists(p) else {"model":os.path.basename(p)[:-5],"noResult":True}
d.update({"loadedContext":ctx,"vramMiBAfterLoad":int(vram),"loadSeconds":int(secs),"armExit":int(rc)})
json.dump(d,open(p,"w"),indent=1)
PY
  lms unload --all >/dev/null 2>&1
  echo "[$(date +%H:%M:%S)] DONE  $m ctx=$loaded vram=${vram}MiB rc=$rc"
  sleep 3
done
echo "[$(date +%H:%M:%S)] ALL DONE"
