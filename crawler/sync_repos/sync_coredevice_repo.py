from sqlalchemy import text

from app.database import get_db
from app.models.core_device import CoreDevice
from app.models.network import Network
from app.schemas.coredevice import CoreDeviceCreate
from app.repositories.coresite_repository import CoreSiteRepository
from app.repositories.network_repository import NetworkRepository
from app.repositories.site_repository import SiteRepository

class CoreDeviceRepository:
    def __init__(self, db=None):
        self.db = db or next(get_db())
        self.coresite_repository = CoreSiteRepository(self.db)
        self.network_repository = NetworkRepository(self.db)
        self.site_repository = SiteRepository(self.db)

    def get_coredevices(self):
        return self.db.query(CoreDevice).all()

    def get_coredevice(self, coredevice_id: int):
        return self.db.query(CoreDevice).filter(CoreDevice.id == coredevice_id).first()

    def get_coredevice_by_ip(self, ip: int):
        return self.db.query(CoreDevice).filter(CoreDevice.ip == ip).first()

    def get_coresite_coredevices(self, coresite_id: int):
        return self.db.query(CoreDevice).filter(CoreDevice.coresite_id == coresite_id).all()

    def create_coredevice(self, coredevice: CoreDeviceCreate, coresite_id: int, network_ids: list[int] = None):
        db_coresite = self.coresite_repository.get_coresite(coresite_id)
        if db_coresite:
            db_coredevice = CoreDevice(name=coredevice.name, ip=coredevice.ip, coresite_id=db_coresite.id)
            self.db.add(db_coredevice)
            self.db.commit()
            self.db.refresh(db_coredevice)

            # Manually add rows to core_device_network_association table
            if network_ids:
                for network_id in network_ids:
                    db_network = self.network_repository.get_network(network_id)
                    if db_network:
                        self.db.execute(text("INSERT INTO core_device_network_association (core_device_id, network_id) VALUES (:core_device_id, :network_id)"),
                                        {"core_device_id": db_coredevice.id, "network_id": network_id})
            else:
                # Use networks from coresite if not specified
                networks = db_coresite.networks
                if not isinstance(db_coresite.networks, list):
                    networks = [db_coresite.networks]
                for db_network in networks:
                    self.db.execute(text("INSERT INTO core_device_network_association (core_device_id, network_id) VALUES (:core_device_id, :network_id)"),
                                    {"core_device_id": db_coredevice.id, "network_id": db_network.id})
            self.db.commit()
            return db_coredevice
        return None

    def get_coresite_coredevices_with_network(self, coresite_id: int, network_id: int):
        return (
            self.db.query(CoreDevice)
                .join(CoreDevice.networks)
                .filter(CoreDevice.coresite_id == coresite_id)
                .filter(Network.id == network_id)
                .all()
        )

    def update_coredevice(self, coredevice_id: int, coredevice: CoreDeviceCreate, network_ids: list[int]):
        db_coredevice = self.db.query(CoreDevice).filter(CoreDevice.id == coredevice_id).first()
        if db_coredevice:
            db_coredevice.name = coredevice.name
            db_coredevice.ip = coredevice.ip

            # Remove existing rows from core_device_network_association table
            self.db.execute(text("DELETE FROM core_device_network_association WHERE core_device_id = :core_device_id"),
                            {"core_device_id": db_coredevice.id})

            # Manually add new rows to core_device_network_association table
            for network_id in network_ids:
                db_network = self.network_repository.get_network(network_id)
                if db_network:
                    self.db.execute(text("INSERT INTO core_device_network_association (core_device_id, network_id) VALUES (:core_device_id, :network_id)"),
                                    {"core_device_id": db_coredevice.id, "network_id": network_id})
            self.db.commit()
            self.db.refresh(db_coredevice)
            return db_coredevice
        return None

    def delete_coredevice(self, coredevice_id: int):
        db_coredevice = self.db.query(CoreDevice).filter(CoreDevice.id == coredevice_id).first()
        if db_coredevice:
            # Remove rows from core_device_network_association table
            self.db.execute(text("DELETE FROM core_device_network_association WHERE core_device_id = :core_device_id"),
                            {"core_device_id": db_coredevice.id})

            # Remove rows from site_coredevice_association table
            self.db.execute(text("DELETE FROM site_coredevice_association WHERE coredevice_id = :coredevice_id"),
                            {"coredevice_id": db_coredevice.id})

            # Delete coredevice
            self.db.delete(db_coredevice)
            self.db.commit()
            return True
        return False

    def get_coredevice_sites(self, coredevice_id: int):
        db_coredevice = self.db.query(CoreDevice).filter(CoreDevice.id == coredevice_id).first()
        if db_coredevice:
            return db_coredevice.sites
        return None
