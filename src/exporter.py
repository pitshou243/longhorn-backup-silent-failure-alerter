#!/usr/bin/env python3
import os
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from kubernetes import client, config
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

NAMESPACE = os.getenv("LONGHORN_NAMESPACE", "longhorn-system")
PORT = int(os.getenv("PORT", "9501"))
ERROR_STATES = {"error", "faulted", "failed", "unknown"}
IN_PROGRESS_STATES = {"inprogress", "in_progress", "pending", "started"}
READY_STATES = {"completed", "complete", "ready"}


def parse_time(value):
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return 0.0


class MetricsHandler(BaseHTTPRequestHandler):
    api = None

    def do_GET(self):
        if self.path not in ("/metrics", "/healthz", "/readyz"):
            self.send_response(404)
            self.end_headers()
            return
        if self.path in ("/healthz", "/readyz"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok\n")
            return
        try:
            payload = collect_metrics(self.api)
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:  # noqa: BLE001
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"metric collection failed: {exc}\n".encode())

    def log_message(self, fmt, *args):
        return


def collect_metrics(api):
    registry = CollectorRegistry()
    scrape_success = Gauge("longhorn_backup_alerter_scrape_success", "Whether the most recent CRD scrape succeeded", registry=registry)
    backup_state = Gauge(
        "longhorn_backup_alerter_backup_state",
        "Backup state as a labeled gauge; exactly one state series is 1 per backup",
        ["namespace", "backup", "volume", "state", "snapshot"],
        registry=registry,
    )
    backup_created = Gauge(
        "longhorn_backup_alerter_backup_created_timestamp_seconds",
        "Backup creation timestamp",
        ["namespace", "backup", "volume"],
        registry=registry,
    )
    backup_completed = Gauge(
        "longhorn_backup_alerter_backup_completed_timestamp_seconds",
        "Backup completion timestamp when available",
        ["namespace", "backup", "volume"],
        registry=registry,
    )
    backup_progress = Gauge(
        "longhorn_backup_alerter_backup_progress_percent",
        "Backup transfer progress percentage",
        ["namespace", "backup", "volume"],
        registry=registry,
    )
    backup_size = Gauge(
        "longhorn_backup_alerter_backup_size_bytes",
        "Backup size reported by the Backup CR",
        ["namespace", "backup", "volume"],
        registry=registry,
    )
    backup_error = Gauge(
        "longhorn_backup_alerter_backup_error_info",
        "Backup error information; value is 1 when an error string is present",
        ["namespace", "backup", "volume", "error"],
        registry=registry,
    )
    last_success = Gauge(
        "longhorn_backup_alerter_volume_last_successful_backup_timestamp_seconds",
        "Most recent successful backup completion timestamp by volume",
        ["namespace", "volume"],
        registry=registry,
    )
    recurring_job = Gauge(
        "longhorn_backup_alerter_recurring_job_info",
        "Configured Longhorn recurring jobs",
        ["namespace", "job", "task", "cron", "retain"],
        registry=registry,
    )

    backups = api.list_namespaced_custom_object("longhorn.io", "v1beta2", NAMESPACE, "backups").get("items", [])
    successful_by_volume = {}
    for item in backups:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        status = item.get("status", {})
        name = metadata.get("name", "unknown")
        volume = spec.get("volumeName") or status.get("volumeName") or metadata.get("labels", {}).get("longhornvolume", "unknown")
        snapshot = spec.get("snapshotName") or status.get("snapshotName") or "unknown"
        raw_state = str(status.get("state") or "unknown")
        state = raw_state.lower().replace("-", "_")
        backup_state.labels(NAMESPACE, name, volume, state, snapshot).set(1)
        created = parse_time(status.get("createdAt") or metadata.get("creationTimestamp"))
        completed = parse_time(status.get("completedAt") or status.get("lastSyncedAt"))
        backup_created.labels(NAMESPACE, name, volume).set(created)
        backup_completed.labels(NAMESPACE, name, volume).set(completed)
        try:
            backup_progress.labels(NAMESPACE, name, volume).set(float(status.get("progress", 0) or 0))
        except (TypeError, ValueError):
            backup_progress.labels(NAMESPACE, name, volume).set(0)
        try:
            backup_size.labels(NAMESPACE, name, volume).set(float(status.get("size", 0) or 0))
        except (TypeError, ValueError):
            backup_size.labels(NAMESPACE, name, volume).set(0)
        error = str(status.get("error") or "").strip()
        if error:
            backup_error.labels(NAMESPACE, name, volume, error[:200]).set(1)
        if state in READY_STATES:
            successful_by_volume[volume] = max(successful_by_volume.get(volume, 0), completed or created)

    for volume, timestamp in successful_by_volume.items():
        last_success.labels(NAMESPACE, volume).set(timestamp)

    jobs = api.list_namespaced_custom_object("longhorn.io", "v1beta2", NAMESPACE, "recurringjobs").get("items", [])
    for item in jobs:
        metadata = item.get("metadata", {})
        spec = item.get("spec", {})
        recurring_job.labels(
            NAMESPACE,
            metadata.get("name", "unknown"),
            str(spec.get("task", "unknown")),
            str(spec.get("cron", "unknown")),
            str(spec.get("retain", "unknown")),
        ).set(1)

    scrape_success.set(1)
    return generate_latest(registry)


def main():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    MetricsHandler.api = client.CustomObjectsApi()
    server = HTTPServer(("0.0.0.0", PORT), MetricsHandler)
    print(f"Listening on :{PORT}; namespace={NAMESPACE}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
