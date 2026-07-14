# Troubleshooting

## Exporter returns HTTP 500

Check permissions and CRD versions:

```bash
kubectl auth can-i list backups.longhorn.io --as system:serviceaccount:longhorn-system:longhorn-backup-alerter -n longhorn-system
kubectl get backups.longhorn.io -n longhorn-system
kubectl logs -n longhorn-system deploy/longhorn-backup-alerter
```

## Prometheus does not discover the target

```bash
kubectl get servicemonitor -n longhorn-system longhorn-backup-alerter -o yaml
kubectl get svc -n longhorn-system longhorn-backup-alerter --show-labels
```

Confirm the `release` label matches the selector used by your Prometheus installation. Rancher Monitoring commonly uses `release: rancher-monitoring`.

## Dashboard panels show no data

Run this query in Prometheus:

```promql
longhorn_backup_alerter_scrape_success
```

If it is absent, fix ServiceMonitor discovery before troubleshooting Grafana.

## NoRecentSuccessfulBackup is too aggressive

Change `86400` in `monitoring/prometheusrule.yaml`. For example, use `172800` for 48 hours. The threshold must match the organization's actual backup schedule.

## Backup state naming differs

Inspect the CR:

```bash
kubectl -n longhorn-system get backups.longhorn.io -o custom-columns=NAME:.metadata.name,STATE:.status.state,VOLUME:.spec.volumeName
```

Add additional normalized states to the alert expression when a Longhorn release uses another terminal state.
