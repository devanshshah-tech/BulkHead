#!/usr/bin/env bash
# OCI Always Free A1 capacity retry loop.
# us-sanjose-1 regularly reports "Out of host capacity" for free ARM shapes;
# capacity frees up as other free-tier users stop instances. This retries
# `terraform apply` on an interval until the VM lands.
#
# Usage: ./hack/oci-retry-apply.sh [interval_seconds]   (default 300)
# Stop:  touch infra/terraform/STOP_RETRY   (or kill the PID in retry.pid)
set -uo pipefail

cd "$(dirname "$0")/../infra/terraform"
INTERVAL="${1:-300}"
MAX_ATTEMPTS=200 # ~16h at default interval
LOG="apply-retry.log"

echo "$(date '+%F %T') retry loop starting (every ${INTERVAL}s, max $MAX_ATTEMPTS)" | tee -a "$LOG"
echo $$ > retry.pid

for i in $(seq 1 "$MAX_ATTEMPTS"); do
  [ -f STOP_RETRY ] && { echo "$(date '+%F %T') stopfile found, exiting" | tee -a "$LOG"; rm -f retry.pid; exit 0; }

  echo "$(date '+%F %T') attempt $i/$MAX_ATTEMPTS" >> "$LOG"
  if terraform apply -auto-approve -no-color >>"$LOG" 2>&1; then
    IP="$(terraform output -raw instance_public_ip 2>/dev/null)"
    echo "$(date '+%F %T') SUCCESS — VM is up at $IP" | tee -a "$LOG"
    rm -f retry.pid
    exit 0
  fi
  grep -q "Out of host capacity" "$LOG" && \
    echo "$(date '+%F %T') still out of capacity" >> "$LOG"

  sleep "$INTERVAL"
done

echo "$(date '+%F %T') gave up after $MAX_ATTEMPTS attempts" | tee -a "$LOG"
rm -f retry.pid
exit 1
