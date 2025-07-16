"""Tests for PII purging utilities."""

from signal_ingestion.privacy import purge_row


def test_purge_row_removes_email() -> None:
    """Ensure email addresses are stripped from content."""
    row = {"content": "Contact me at user@example.com"}
    cleaned = purge_row(row)
    assert "user@example.com" not in cleaned["content"]


def test_purge_row_removes_phone() -> None:
    """Ensure phone numbers are stripped from content."""
    row = {"content": "Call 123-456-7890 now"}
    cleaned = purge_row(row)
    assert "123-456-7890" not in cleaned["content"]
