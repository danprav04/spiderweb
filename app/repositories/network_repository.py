# app/repositories/network_repository.py

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.core_site import CoreSite
from app.models.network import Network
from app.schemas.network import NetworkCreate


class NetworkRepository:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def get_networks(self) -> List[Network]:
        stmt = select(Network)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_coresites(self, network_id: int) -> List[CoreSite]:
        stmt = select(CoreSite).join(CoreSite.networks).where(Network.id == network_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_network(self, network_id: int) -> Optional[Network]:
        stmt = select(Network).where(Network.id == network_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_network(self, network: NetworkCreate) -> Network:
        db_network = Network(name=network.name)
        self.db.add(db_network)
        await self.db.commit()
        await self.db.refresh(db_network)
        return db_network

    async def update_network(self, network_id: int, network: NetworkCreate) -> Optional[Network]:
        db_network = await self.get_network(network_id)
        if db_network:
            db_network.name = network.name
            await self.db.commit()
            await self.db.refresh(db_network)
            return db_network
        return None

    async def delete_network(self, network_id: int) -> bool:
        db_network = await self.get_network(network_id)
        if db_network:
            # Check if network is associated with any coresite or coredevice
            if db_network.core_sites or db_network.core_devices:
                return False  # Do not delete if associated with coresite or coredevice
            await self.db.delete(db_network)
            await self.db.commit()
            return True
        return False