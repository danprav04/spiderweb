from sqlalchemy import text

from app.database import get_async_db
from app.models.core_site import CoreSite
from app.schemas.coresite import CoreSiteCreate
from app.repositories.network_repository import NetworkRepository

class CoreSiteRepository:
    def __init__(self, db=None):
        self.db = db or next(get_db())
        self.network_repository = NetworkRepository(self.db)

    def get_coresites(self):
        return self.db.query(CoreSite).all()

    def get_coresite(self, coresite_id: int):
        return self.db.query(CoreSite).filter(CoreSite.id == coresite_id).first()

    def create_coresite(self, coresite: CoreSiteCreate, network_ids: list[int]):
        db_coresite = CoreSite(name=coresite.name)
        self.db.add(db_coresite)
        self.db.commit()
        self.db.refresh(db_coresite)

        # Manually add rows to core_site_network_association table
        for network_id in network_ids:
            db_network = self.network_repository.get_network(network_id)
            if db_network:
                self.db.execute(text("INSERT INTO core_site_network_association (core_site_id, network_id) VALUES (:core_site_id, :network_id)"),
                                {"core_site_id": db_coresite.id, "network_id": network_id})
        self.db.commit()
        return db_coresite

    def update_coresite(self, coresite_id: int, coresite: CoreSiteCreate, network_ids: list[int]):
        db_coresite = self.db.query(CoreSite).filter(CoreSite.id == coresite_id).first()
        if db_coresite:
            db_coresite.name = coresite.name

            # Remove existing rows from core_site_network_association table
            self.db.execute(text("DELETE FROM core_site_network_association WHERE core_site_id = :core_site_id"),
                            {"core_site_id": db_coresite.id})

            # Manually add new rows to core_site_network_association table
            for network_id in network_ids:
                db_network = self.network_repository.get_network(network_id)
                if db_network:
                    self.db.execute(text("INSERT INTO core_site_network_association (core_site_id, network_id) VALUES (:core_site_id, :network_id)"),
                                    {"core_site_id": db_coresite.id, "network_id": network_id})
            self.db.commit()
            self.db.refresh(db_coresite)
            return db_coresite
        return None

    def delete_coresite(self, coresite_id: int):
        db_coresite = self.db.query(CoreSite).filter(CoreSite.id == coresite_id).first()
        if db_coresite:
            # Remove rows from core_site_network_association table
            self.db.execute(text("DELETE FROM core_site_network_association WHERE core_site_id = :core_site_id"),
                            {"core_site_id": db_coresite.id})

            # Delete coresite
            self.db.delete(db_coresite)
            self.db.commit()
            return True
        return False
