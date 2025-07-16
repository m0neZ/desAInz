"""FastAPI application for marketplace publisher."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException

from .db import engine, get_session
from .models import Base, PublishJob, PublishState
from .services import publish_to_amazon, publish_to_etsy, publish_to_redbubble


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Marketplace Publisher", lifespan=lifespan)


async def _publish(marketplace: str, data: Dict[str, Any]) -> str:
    """Publish to the specified marketplace with retry logic."""
    attempts = 0
    while attempts < 3:
        try:
            if marketplace == "redbubble":
                return await publish_to_redbubble(data)
            if marketplace == "amazon":
                return await publish_to_amazon(data)
            if marketplace == "etsy":
                return await publish_to_etsy(data)
            raise HTTPException(status_code=400, detail="Unknown marketplace")
        except Exception:
            attempts += 1
            await asyncio.sleep(2**attempts)
    raise HTTPException(status_code=500, detail="Publish failed")


@app.post("/publish/{marketplace}")
async def publish(
    marketplace: str, data: Dict[str, Any], session=Depends(get_session)
) -> Dict[str, Any]:
    """Endpoint to publish design to marketplace."""
    job = PublishJob(marketplace=marketplace, state=PublishState.IN_PROGRESS)
    session.add(job)
    await session.commit()
    try:
        listing_id = await _publish(marketplace, data)
        job.listing_id = str(listing_id)  # type: ignore[assignment]
        job.state = PublishState.SUCCESS
    except HTTPException:
        job.state = PublishState.FAILED
        raise
    finally:
        await session.commit()
    return {"job_id": job.id, "listing_id": job.listing_id}


@app.get("/publish/{job_id}")
async def job_status(job_id: int, session=Depends(get_session)) -> Dict[str, Any]:
    """Get the status of a publish job."""
    job = await session.get(PublishJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job.id, "state": job.state.value, "listing_id": job.listing_id}
