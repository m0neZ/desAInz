"""Tests for feedback loop scheduler."""

from pathlib import Path
import sys
import importlib.util

from apscheduler.triggers.cron import CronTrigger

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT.parent))
sys.path.append(str(ROOT / "feedback-loop"))

SPEC = importlib.util.spec_from_file_location(
    "feedback_loop.scheduler",
    ROOT / "feedback-loop" / "feedback_loop" / "scheduler.py",
)
scheduler_mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(scheduler_mod)

setup_scheduler = scheduler_mod.setup_scheduler


def test_nightly_update_schedule() -> None:
    """Nightly update should run at 00:05."""
    scheduler = setup_scheduler([], "http://api")
    job = next(j for j in scheduler.get_jobs() if j.func.__name__ == "nightly_update")
    assert isinstance(job.trigger, CronTrigger)
    assert job.trigger.fields[5].expressions[0].start == 0  # hour
    assert job.trigger.fields[6].expressions[0].start == 5  # minute
