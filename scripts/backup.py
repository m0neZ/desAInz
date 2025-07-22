"""Backup the PostgreSQL database to S3."""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for backup destinations and database."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    pgdatabase: str = Field(default="app", alias="PGDATABASE")
    backup_bucket: str = Field(default="", alias="BACKUP_BUCKET")
    backup_dir: Path = Field(default=Path("/tmp"), alias="BACKUP_DIR")


settings = Settings()


def run(command: list[str]) -> None:
    """Run a command and raise an error if it fails."""
    subprocess.run(command, check=True)


def dump_postgres(backup_dir: Path, bucket: str) -> None:
    """
    Dump the Postgres database and upload it to S3.

    Parameters
    ----------
    backup_dir : Path
        Directory to store the dump.
    bucket : str
        Name of the S3 bucket.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    dump_file = backup_dir / f"postgres_{timestamp}.sql"
    run(["pg_dump", settings.pgdatabase, "-f", str(dump_file)])
    run(["aws", "s3", "cp", str(dump_file), f"s3://{bucket}/postgres/{dump_file.name}"])
    dump_file.unlink()


def main() -> None:
    """Run database backups."""
    backup_dir = settings.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    dump_postgres(backup_dir, settings.backup_bucket)


if __name__ == "__main__":
    main()
