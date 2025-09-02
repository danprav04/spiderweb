from sqlalchemy import Column, Integer, Table
from sqlalchemy.orm import Mapped

from app.models import Base


class CrawlerCycle(Base):
    """
    Crawler cycle model
    """
    __tablename__ = "crawler_cycles"
    id: int = Column(Integer, primary_key=True)
    count: int = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"CrawlerCycle(count='{self.count}')"
