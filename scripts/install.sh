#!/usr/bin/env bash
set -euo pipefail
IMAGE="${IMAGE:-ghcr.io/REPLACE_ME/longhorn-backup-silent-failure-alerter:latest}"
kubectl apply -f deploy/all-in-one.yaml
kubectl -n longhorn-system set image deployment/longhorn-backup-alerter exporter="$IMAGE"
kubectl apply -f monitoring/servicemonitor.yaml
kubectl apply -f monitoring/prometheusrule.yaml
kubectl -n longhorn-system rollout status deployment/longhorn-backup-alerter --timeout=180s
