#!/bin/bash
# Waits for the running p3f r1 pass of round 13 (summary.json), then runs v13.sh, which skips finished passes and runs control r1. Owner's yes: 2026-11-20 ("ok continua"); cap raised to 14 USD estimated for this step.
cd "$(dirname "$0")"
until [ -s night13/mercury-3/bench-p3f-r1/summary.json ]; do sleep 20; done
echo "$(date -Is) owner said continue: resuming v13 for control r1, estimated cap 14 USD" >> night13/progress.txt
CAP_USD=14 exec ./v13.sh
