#!/usr/bin/env bash
# One model at a time, everything unloaded between, load settings pinned.
#
#   ./run_all.sh <model-key> [<model-key> ...]          one run each
#   RUNS=3 ./run_all.sh <model-key> ...                  three runs each (recommended)
#
# Why the flags matter: without --gpu, LM Studio picks the offload ratio itself and can
# silently split a model between GPU and CPU, which changes the speed you measure.
# --gpu max makes a model that does not fit fail to load instead of being mis-timed.
# CTX and PARALLEL are defaults, not necessarily what earlier published runs used.
set -u
CTX="${CTX:-32768}"
PARALLEL="${PARALLEL:-1}"
RUNS="${RUNS:-1}"
HERE="$(cd "$(dirname "$0")" && pwd)"
for model in "$@"; do
  echo "=== $model"
  lms unload --all >/dev/null 2>&1
  if ! lms load "$model" --gpu max --context-length "$CTX" --parallel "$PARALLEL" -y >/dev/null 2>&1; then
    echo "  could not load (does it fit with --gpu max at ${CTX} context?) - skipped"
    continue
  fi
  for run in $(seq 1 "$RUNS"); do
    python3 "$HERE/run_grid.py" "$model" "$run"
  done
done
lms unload --all >/dev/null 2>&1
echo "ALL-DONE"
