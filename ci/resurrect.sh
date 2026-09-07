#!/usr/bin/env bash
# resurrect guard: 一败一挽。仅 failure/timed_out 挽;cancelled/skipped 不挽(被取代非死);
# 连败(前拍非success)不挽→烽火告警即眠。
set -u
CONC="$1"; RUN_ID="$2"
case "$CONC" in
  failure|timed_out|startup_failure) : ;;
  *) echo "conclusion=$CONC not resurrectable (cancelled/skipped=superseded)"; exit 0;;
esac
PREV=$(curl -sS -H "Authorization: token $GH_PAT" -H "Accept: application/vnd.github+json"   "https://api.github.com/repos/chepin-qi/qfa-pub/actions/workflows/engine.yml/runs?per_page=8&status=completed"   | RUN_ID="$RUN_ID" python3 - <<'PYEOF'
import json,sys,os
runs=json.load(sys.stdin)['workflow_runs']
others=[r for r in runs if str(r['id'])!=os.environ['RUN_ID']]
print(others[0]['conclusion'] if others else 'none')
PYEOF
)
echo "prev completed conclusion: $PREV"
if [ "$PREV" = "success" ]; then
  curl -sS -X POST -H "Authorization: token $GH_PAT" -H "Accept: application/vnd.github+json"     https://api.github.com/repos/chepin-qi/qfa-pub/dispatches     -d "{"event_type":"qfa-beat","client_payload":{"reason":"resurrect:$RUN_ID","resurrect_run":"$RUN_ID"}}"
  echo "resurrect fired for run $RUN_ID"
else
  curl -sS -X POST -H "Authorization: token $GH_PAT" -H "Accept: application/vnd.github+json"     https://api.github.com/repos/chepin-qi/qi-lab/issues/5/comments     -d "{"body":"[qfa resurrector 告警] engine 连败(run $RUN_ID,前拍=$PREV),一败一挽律止挽即眠——候人/事件介入。#noauto"}"
  echo "consecutive failure; beacon alert, stay dead"
fi
