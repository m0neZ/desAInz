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


def test_purge_row_removes_address() -> None:
    """Ensure street addresses are stripped from content."""
    row = {"content": "Meet me at 123 Main St"}
    cleaned = purge_row(row)
    assert "123 Main St" not in cleaned["content"]


def test_purge_row_removes_credit_card() -> None:
    """Ensure credit card numbers are stripped from content."""
    row = {"content": "Card 4111 1111 1111 1111"}
    cleaned = purge_row(row)
    assert "4111 1111 1111 1111" not in cleaned["content"]


def test_purge_row_removes_name() -> None:
    """Ensure names are stripped from content."""
    row = {"content": "Signed, John Smith"}
    cleaned = purge_row(row)
    assert "John Smith" not in cleaned["content"]
