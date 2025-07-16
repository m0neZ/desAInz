"""API routes including REST and tRPC-compatible endpoints."""

from typing import Any, Dict, Iterable

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import csv
from io import StringIO
from sqlalchemy import func, select

from backend.shared.db import session_scope
from backend.shared.db.models import ABTest, Listing

from .auth import require_role, verify_token

router = APIRouter()


@router.get("/status")
async def status() -> Dict[str, str]:
    """Public status endpoint."""
    return {"status": "ok"}


@router.get("/protected")
async def protected(
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """Protected endpoint requiring a valid token."""
    return {"user": payload.get("sub")}


@router.post("/trpc/{procedure}")
async def trpc_endpoint(
    procedure: str,
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """tRPC-compatible endpoint."""
    if procedure == "ping":
        return {"result": {"message": "pong", "user": payload.get("sub")}}
    return {"error": f"Procedure '{procedure}' not found"}


def _rows_to_csv(rows: Iterable[Iterable[Any]], headers: list[str]) -> str:
    """Convert iterable rows to CSV string."""
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


@router.get("/export/ab_tests")
async def export_ab_tests(
    _payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StreamingResponse:
    """Return A/B test results as a CSV file."""
    with session_scope() as session:
        rows = session.execute(
            select(ABTest.id, ABTest.listing_id, ABTest.variant, ABTest.conversion_rate)
        ).all()

    csv_content = _rows_to_csv(rows, ["id", "listing_id", "variant", "conversion_rate"])
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ab_tests.csv"},
    )


@router.get("/export/marketplace_stats")
async def export_marketplace_stats(
    _payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StreamingResponse:
    """Return marketplace listing statistics as a CSV file."""
    with session_scope() as session:
        rows = session.execute(
            select(
                Listing.id,
                Listing.price,
                func.count(ABTest.id).label("num_tests"),
            )
            .join(ABTest, ABTest.listing_id == Listing.id, isouter=True)
            .group_by(Listing.id)
        ).all()
    csv_content = _rows_to_csv(rows, ["listing_id", "price", "num_tests"])
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=marketplace_stats.csv"},
    )
