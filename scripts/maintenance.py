"""Scheduled maintenance tasks for desAInz."""

from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

from backend.shared.db import session_scope
from backend.shared.db.models import AuditLog, Mockup, Signal

logger = logging.getLogger(__name__)

COLD_STORAGE_PATH = Path(os.environ.get("COLD_STORAGE_PATH", "cold_storage"))
LOG_DIR = Path(os.environ.get("LOG_DIR", "logs"))


def archive_old_mockups() -> None:
    """Move mockups older than 12 months to cold storage and remove records."""
    cutoff = datetime.utcnow() - timedelta(days=365)
    COLD_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    with session_scope() as session:
        old_mockups = session.query(Mockup).filter(Mockup.created_at < cutoff).all()
        for mockup in old_mockups:
            image_path = Path(mockup.image_url)
            if image_path.exists():
                archive_path = COLD_STORAGE_PATH / image_path.name
                logger.info("Archiving %s to %s", image_path, archive_path)
                shutil.move(image_path, archive_path)
            session.delete(mockup)
        logger.info("Archived and removed %s mockups", len(old_mockups))


def purge_stale_records() -> None:
    """Delete signals and log files older than 30 days."""
    cutoff = datetime.utcnow() - timedelta(days=30)
    with session_scope() as session:
        deleted = (
            session.query(Signal)
            .filter(Signal.timestamp < cutoff)
            .delete(synchronize_session=False)
        )
        logger.info("Deleted %s stale signals", deleted)
    if LOG_DIR.exists():
        for path in LOG_DIR.glob("*.log"):
            if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                logger.info("Removing old log file %s", path)
                path.unlink()


def purge_old_audit_logs() -> None:
    """Delete audit log entries older than 18 months."""
    cutoff = datetime.utcnow() - timedelta(days=30 * 18)
    with session_scope() as session:
        deleted = (
            session.query(AuditLog)
            .filter(AuditLog.timestamp < cutoff)
            .delete(synchronize_session=False)
        )
        logger.info("Deleted %s audit logs", deleted)


def purge_old_s3_objects(retention_days: int = 90) -> None:
    """
    Delete objects from the configured S3 bucket older than ``retention_days``.

    The bucket and credentials are loaded from :mod:`backend.shared.config.settings`.
    If no bucket is configured the routine exits silently.
    """
    from backend.shared.config import settings

    if not settings.s3_bucket:
        logger.info("s3_bucket not configured; skipping S3 purge")
        return

    try:
        import boto3
    except ImportError:  # pragma: no cover - dependency missing
        logger.warning("boto3 not installed; cannot purge S3 objects")
        return

    client_params: Dict[str, Any] = {}
    if settings.s3_endpoint:
        client_params["endpoint_url"] = settings.s3_endpoint
    if settings.s3_access_key and settings.s3_secret_key:
        client_params["aws_access_key_id"] = settings.s3_access_key
        client_params["aws_secret_access_key"] = settings.s3_secret_key

    s3 = boto3.client("s3", **client_params)
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=settings.s3_bucket):
        for obj in page.get("Contents", []):
            last_modified = obj.get("LastModified")
            if last_modified and last_modified.replace(tzinfo=None) < cutoff:
                key = obj["Key"]
                logger.info("Removing S3 object %s", key)
                s3.delete_object(Bucket=settings.s3_bucket, Key=key)


def setup_scheduler() -> BlockingScheduler:
    """Return a scheduler configured for maintenance tasks."""
    scheduler = BlockingScheduler()
    scheduler.add_job(archive_old_mockups, "cron", hour=2, minute=0)
    scheduler.add_job(purge_stale_records, "cron", hour=3, minute=0)
    scheduler.add_job(purge_old_audit_logs, "cron", hour=4, minute=0)
    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler = setup_scheduler()
    scheduler.start()
