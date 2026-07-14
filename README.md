# Longhorn Backup Silent-Failure Alerter

Prometheus alerts and a Grafana dashboard for Longhorn backups that fail, stall, or stop reaching the configured S3/NFS backup target.

## Why a custom exporter?

Longhorn exposes Prometheus metrics from `longhorn-manager`, but backup lifecycle fields are primarily represented in Longhorn Backup CRDs. This project reads those CRDs and exposes stable backup-specific metrics instead of assuming undocumented native metric names.

## Included

- Read-only CRD exporter
- Rancher Monitoring-compatible `ServiceMonitor`
- `PrometheusRule` alerts
- Grafana dashboard
- RBAC and Kubernetes deployment
- GHCR build workflow
- CI validation workflow
- Installation and validation scripts

## Alerts

| Alert | Default condition | Severity |
|---|---|---|
| `LonghornBackupAlerterDown` | Exporter absent for 10 minutes | Critical |
| `LonghornBackupError` | Backup in an error/failure state for 5 minutes | Critical |
| `LonghornBackupStuckInProgress` | Backup active for more than 2 hours | Warning |
| `LonghornBackupProgressStalled` | Progress unchanged for 30 minutes | Warning |
| `LonghornNoRecentSuccessfulBackup` | No success for 24 hours | Warning |

Review the thresholds before production use, especially the 24-hour policy alert.

## Repository layout

```text
.
├── deploy/all-in-one.yaml
├── monitoring/
│   ├── prometheusrule.yaml
│   └── servicemonitor.yaml
├── grafana/longhorn-backup-dashboard.json
├── src/exporter.py
├── scripts/install.sh
├── scripts/validate.sh
├── docs/
├── Dockerfile
└── .github/workflows/
```

## Build and publish

Push this repository to GitHub. The container workflow publishes images to:

```text
ghcr.io/<owner>/<repository>:main
```

Replace `REPLACE_ME` in `deploy/all-in-one.yaml`, or install with:

```bash
IMAGE=ghcr.io/<owner>/<repository>:main ./scripts/install.sh
```

## Manual installation

```bash
kubectl apply -f deploy/all-in-one.yaml
kubectl -n longhorn-system set image deployment/longhorn-backup-alerter \
  exporter=ghcr.io/<owner>/<repository>:main
kubectl apply -f monitoring/servicemonitor.yaml
kubectl apply -f monitoring/prometheusrule.yaml
```

## Verify

```bash
./scripts/validate.sh
```

Or query Prometheus:

```promql
longhorn_backup_alerter_scrape_success
```

Expected result: `1`.

## Import the Grafana dashboard

In Grafana, select **Dashboards → New → Import**, then upload:

```text
grafana/longhorn-backup-dashboard.json
```

Select the Prometheus data source when prompted.

## Compatibility

The exporter expects Longhorn `v1beta2` Backup and RecurringJob CRDs. Validate against the Longhorn release used by the target cluster before rollout.

## Security

The deployment uses a namespace-scoped Role with read-only access to `backups.longhorn.io` and `recurringjobs.longhorn.io`. It runs as non-root with a read-only root filesystem and no Linux capabilities.

## Documentation

- [Metrics](docs/METRICS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## License

Apache-2.0
