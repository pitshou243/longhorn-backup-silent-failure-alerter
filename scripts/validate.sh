#!/usr/bin/env bash
set -euo pipefail
NS="${LONGHORN_NAMESPACE:-longhorn-system}"
printf '%s\n' '== CRDs =='
kubectl get crd backups.longhorn.io recurringjobs.longhorn.io
printf '%s\n' '== Workload =='
kubectl -n "$NS" get deploy,svc,servicemonitor,prometheusrule -l app.kubernetes.io/name=longhorn-backup-alerter 2>/dev/null || true
printf '%s\n' '== Metrics sample =='
kubectl -n "$NS" port-forward svc/longhorn-backup-alerter 9501:9501 >/tmp/lh-backup-alerter-pf.log 2>&1 &
PF_PID=$!
trap 'kill "$PF_PID" 2>/dev/null || true' EXIT
sleep 2
curl -fsS http://127.0.0.1:9501/metrics | grep '^longhorn_backup_alerter_' | head -40
