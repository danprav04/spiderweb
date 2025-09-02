from app.database import get_async_db
from app.models.crawler_cycle import CrawlerCycle

class CrawlerCycleRepository:
    def __init__(self, db=None):
        self.db = db or next(get_db())

    def get_crawler_cycle(self):
        return self.db.query(CrawlerCycle).first()

    def increment_crawler_cycle(self):
        """Increments the crawler cycle count by 1. If no cycle exists, creates a new one with count 0."""
        crawler_cycle = self.get_crawler_cycle()
        if crawler_cycle:
            crawler_cycle.count += 1
        else:
            # Create a new cycle starting at 0, then increment it to 1
            crawler_cycle = CrawlerCycle(count=0)
            self.db.add(crawler_cycle)
            self.db.commit()  # Commit here so we can safely increment below
            crawler_cycle.count = 1  # Now set it to 1 after committing

        self.db.commit()