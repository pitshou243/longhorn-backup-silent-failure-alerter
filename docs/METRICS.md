# Metrics

| Metric | Description |
|---|---|
| `longhorn_backup_alerter_scrape_success` | `1` when the exporter can list Longhorn CRDs. |
| `longhorn_backup_alerter_backup_state` | One labeled series per backup state. |
| `longhorn_backup_alerter_backup_created_timestamp_seconds` | Backup creation time. |
| `longhorn_backup_alerter_backup_completed_timestamp_seconds` | Completion or last synchronization time. |
| `longhorn_backup_alerter_backup_progress_percent` | Transfer progress reported by Longhorn. |
| `longhorn_backup_alerter_backup_size_bytes` | Backup size reported by Longhorn. |
| `longhorn_backup_alerter_backup_error_info` | Error text exposed as an informational label. |
| `longhorn_backup_alerter_volume_last_successful_backup_timestamp_seconds` | Latest successful backup by volume. |
| `longhorn_backup_alerter_recurring_job_info` | Recurring job task, cron, and retention configuration. |

The exporter reads `backups.longhorn.io` and `recurringjobs.longhorn.io` in `longhorn-system`. It does not modify Longhorn resources.
