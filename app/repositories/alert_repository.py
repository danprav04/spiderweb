# app/repositories/alert_repository.py

from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert import Alert
from app.models.crawler_cycle import CrawlerCycle


class AlertRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_alerts(self, last_crawl_number: int = 0) -> List[Dict]:
        current_crawl_number = await self.db.scalar(
            CrawlerCycle.__table__.select().with_only_columns(CrawlerCycle.count).limit(1)
        )
        if last_crawl_number >= current_crawl_number:
            return []
        stmt = Alert.__table__.select().where(
            (Alert.crawl_number >= last_crawl_number) &
            (Alert.crawl_number <= current_crawl_number)
        )
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        # Get column names from the result
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]

    async def get_current_crawl_number(self) -> int:
        stmt = CrawlerCycle.__table__.select().with_only_columns(CrawlerCycle.count).limit(1)
        return await self.db.scalar(stmt)

    async def get_all_alerts(self) -> List[Dict]:
        stmt = Alert.__table__.select()
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        return [dict(row) for row in rows]

    async def get_alert(self, alert_id: int) -> Dict:
        stmt = Alert.__table__.select().where(Alert.id == alert_id)
        result = await self.db.execute(stmt)
        row = result.fetchone()
        return dict(row) if row else None
