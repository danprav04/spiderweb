# main.py or wherever routes are defined
import asyncio
import time

from fastapi import Depends, APIRouter, Request
from app.database import get_async_db
from app.repositories.alert_repository import AlertRepository
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Create the router instance
router = APIRouter()


async def poll_for_new_alerts(last_crawl_number: int, db: AsyncSession, timeout: int = 600):
    """Blocking function that polls for new alerts"""
    alert_repository = AlertRepository(db)
    start_time = time.time()

    while True:
        current_crawl = await alert_repository.get_current_crawl_number()
        if current_crawl > last_crawl_number:
            alerts = await alert_repository.get_alerts(last_crawl_number)
            return {"alerts": alerts, "current_crawl_number": current_crawl}

        if time.time() - start_time > timeout:
            return {"error": "timeout"}

        await asyncio.sleep(5)


@router.get("/alerts")
async def get_alerts(
    request: Request,
    last_crawl_number: int = None,
    db: AsyncSession = Depends(get_async_db)
):
    if last_crawl_number is None:
        current_crawl = await AlertRepository(db).get_current_crawl_number()
        return JSONResponse(
            content={
                "error": "last_crawl_number is required",
                "current_crawl_number": current_crawl
            },
            status_code=400
        )

    try:
        result = await poll_for_new_alerts(last_crawl_number, db)
        return result
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
