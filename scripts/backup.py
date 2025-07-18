"""Backup the PostgreSQL database to S3."""

import os
import subprocess
from datetime import datetime
from pathlib import Path


def run(command: list[str]) -> None:
    """Run a command and raise an error if it fails."""
    subprocess.run(command, check=True)


def dump_postgres(backup_dir: Path, bucket: str) -> None:
    """
    Dump Postgres database and upload to S3.

    Args:
        backup_dir: Directory to store the dump.
        bucket: Name of the S3 bucket.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    dump_file = backup_dir / f"postgres_{timestamp}.sql"
    run(
        [
            "pg_dump",
            os.getenv("PGDATABASE", "app"),
            "-f",
            str(dump_file),
        ]
    )
    run(["aws", "s3", "cp", str(dump_file), f"s3://{bucket}/postgres/{dump_file.name}"])
    dump_file.unlink()


def main() -> None:
    """Run database backups."""
    bucket = os.environ["BACKUP_BUCKET"]
    backup_dir = Path(os.getenv("BACKUP_DIR", "/tmp"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    dump_postgres(backup_dir, bucket)


if __name__ == "__main__":
    main()
