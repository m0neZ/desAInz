"""Tests for score_updater."""

from unittest import mock

from feedback_loop.score_updater import schedule_score_update_job, update_weights


def test_update_weights_calls_api() -> None:
    """Ensure API call is made when updating weights."""
    with mock.patch("requests.post") as post:
        update_weights("http://example.com", {"w": 1.0})
        post.assert_called_once()


def test_schedule_job_returns_scheduler() -> None:
    """Ensure scheduler is returned with job."""
    sched = schedule_score_update_job("url", {"w": 1.0})
    job = sched.get_job("score_weight_update")
    assert job is not None
