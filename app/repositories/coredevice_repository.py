from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_async_db
from app.models.core_device import CoreDevice
from app.models.network import Network
from app.schemas.coredevice import CoreDeviceCreate
from app.repositories.coresite_repository import CoreSiteRepository
from app.repositories.network_repository import NetworkRepository
from app.repositories.site_repository import SiteRepository


class CoreDeviceRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db
        if not self.db:
            raise ValueError("A database session must be provided.")
        self.coresite_repository = CoreSiteRepository(self.db)
        self.network_repository = NetworkRepository(self.db)
        self.site_repository = SiteRepository(self.db)

    async def get_coredevices(self):
        stmt = select(CoreDevice)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_coredevice(self, coredevice_id: int):
        stmt = select(CoreDevice).where(CoreDevice.id == coredevice_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_coredevice_by_ip(self, ip: int):
        stmt = select(CoreDevice).where(CoreDevice.ip == ip)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_coresite_coredevices(self, coresite_id: int):
        stmt = select(CoreDevice).where(CoreDevice.coresite_id == coresite_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_coredevice(self, coredevice: CoreDeviceCreate, coresite_id: int, network_ids: list[int] = None):
        db_coresite = await self.coresite_repository.get_coresite(coresite_id)
        if db_coresite:
            db_coredevice = CoreDevice(name=coredevice.name, ip=coredevice.ip, coresite_id=db_coresite.id)
            self.db.add(db_coredevice)
            await self.db.commit()
            await self.db.refresh(db_coredevice)

            # Manually add rows to core_device_network_association table
            if network_ids:
                for network_id in network_ids:
                    db_network = await self.network_repository.get_network(network_id)
                    if db_network:
                        await self.db.execute(text(
                            "INSERT INTO core_device_network_association (core_device_id, network_id) VALUES (:core_device_id, :network_id)"),
                            {"core_device_id": db_coredevice.id, "network_id": network_id})
            else:
                # Use networks from coresite if not specified
                networks = db_coresite.networks
                if not isinstance(db_coresite.networks, list):
                    networks = [db_coresite.networks]
                for db_network in networks:
                    await self.db.execute(text(
                        "INSERT INTO core_device_network_association (core_device_id, network_id) VALUES (:core_device_id, :network_id)"),
                        {"core_device_id": db_coredevice.id, "network_id": db_network.id})

            await self.db.commit()
            return db_coredevice
        return None

    async def get_coresite_coredevices_with_network(self, coresite_id: int, network_id: int):
        # Fixed: Properly filter CoreDevices that have the specified network
        stmt = select(CoreDevice).where(
            CoreDevice.coresite_id == coresite_id,
            CoreDevice.networks.any(Network.id == network_id)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_coredevice(self, coredevice_id: int, coredevice: CoreDeviceCreate, network_ids: list[int]):
        db_coredevice = await self.get_coredevice(coredevice_id)
        if db_coredevice:
            db_coredevice.name = coredevice.name
            db_coredevice.ip = coredevice.ip

            # Remove existing rows from core_device_network_association table
            await self.db.execute(
                text("DELETE FROM core_device_network_association WHERE core_device_id = :core_device_id"),
                {"core_device_id": db_coredevice.id})

            # Manually add new rows to core_device_network_association table
            for network_id in network_ids:
                db_network = await self.network_repository.get_network(network_id)
                if db_network:
                    await self.db.execute(text(
                        "INSERT INTO core_device_network_association (core_device_id, network_id) VALUES (:core_device_id, :network_id)"),
                        {"core_device_id": db_coredevice.id, "network_id": network_id})

            await self.db.commit()
            await self.db.refresh(db_coredevice)
            return db_coredevice
        return None

    async def delete_coredevice(self, coredevice_id: int):
        db_coredevice = await self.get_coredevice(coredevice_id)
        if db_coredevice:
            # Remove rows from core_device_network_association table
            await self.db.execute(
                text("DELETE FROM core_device_network_association WHERE core_device_id = :core_device_id"),
                {"core_device_id": db_coredevice.id})

            # Remove rows from site_coredevice_association table
            await self.db.execute(text("DELETE FROM site_coredevice_association WHERE coredevice_id = :coredevice_id"),
                                  {"coredevice_id": db_coredevice.id})

            # Delete coredevice
            await self.db.delete(db_coredevice)
            await self.db.commit()
            return True
        return False

    async def get_coredevice_sites(self, coredevice_id: int):
        db_coredevice = await self.get_coredevice(coredevice_id)
        if db_coredevice:
            return db_coredevice.sites
        return None