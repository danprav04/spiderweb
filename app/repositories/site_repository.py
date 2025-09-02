from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_async_db
from app.models.core_device import CoreDevice
from app.models.site import Site
from app.models.link import Link
from app.schemas.site import SiteCreate
from typing import List, Optional


class SiteRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def get_sites(self) -> List[Site]:
        if not self.db:
            async with get_async_db() as db:
                result = await db.execute(text("SELECT * FROM sites"))
                return result.fetchall()
        result = await self.db.execute(text("SELECT * FROM sites"))
        return result.fetchall()

    async def get_site(self, site_id: int) -> Optional[Site]:
        if not self.db:
            async with get_async_db() as db:
                result = await db.execute(text("SELECT * FROM sites WHERE id = :site_id"), {"site_id": site_id})
                return result.fetchone()
        result = await self.db.execute(text("SELECT * FROM sites WHERE id = :site_id"), {"site_id": site_id})
        return result.fetchone()

    async def get_sites_of_coredevice(self, coredevice_id: int) -> List[Site]:
        if not self.db:
            async with get_async_db() as db:
                result = await db.execute(
                    text("""
                        SELECT s.* FROM sites s 
                        JOIN site_coredevice_association sca ON s.id = sca.site_id 
                        WHERE sca.coredevice_id = :coredevice_id
                    """),
                    {"coredevice_id": coredevice_id}
                )
                return result.fetchall()
        result = await self.db.execute(
            text("""
                SELECT s.* FROM sites s 
                JOIN site_coredevice_association sca ON s.id = sca.site_id 
                WHERE sca.coredevice_id = :coredevice_id
            """),
            {"coredevice_id": coredevice_id}
        )
        return result.fetchall()

    async def create_site(self, site: SiteCreate, coredevice_id: int) -> Optional[Site]:
        if not self.db:
            async with get_async_db() as db:
                # Create site
                result = await db.execute(
                    text("""
                        INSERT INTO sites (name, topology, description) 
                        VALUES (:name, :topology, :description) 
                        RETURNING *
                    """),
                    {
                        "name": site.name,
                        "topology": site.topology,
                        "description": site.description
                    }
                )
                db_site = result.fetchone()

                # Associate with core device
                await db.execute(
                    text(
                        "INSERT INTO site_coredevice_association (site_id, coredevice_id) VALUES (:site_id, :coredevice_id)"),
                    {"site_id": db_site.id, "coredevice_id": coredevice_id}
                )

                await db.commit()
                return db_site

        # Create site
        result = await self.db.execute(
            text("""
                INSERT INTO sites (name, topology, description) 
                VALUES (:name, :topology, :description) 
                RETURNING *
            """),
            {
                "name": site.name,
                "topology": site.topology,
                "description": site.description
            }
        )
        db_site = result.fetchone()

        # Associate with core device
        await self.db.execute(
            text("INSERT INTO site_coredevice_association (site_id, coredevice_id) VALUES (:site_id, :coredevice_id)"),
            {"site_id": db_site.id, "coredevice_id": coredevice_id}
        )

        await self.db.commit()
        return db_site

    async def update_site(self, site_id: int, site: SiteCreate) -> Optional[Site]:
        if not self.db:
            async with get_async_db() as db:
                result = await db.execute(
                    text("""
                        UPDATE sites 
                        SET name = :name, topology = :topology, description = :description 
                        WHERE id = :site_id 
                        RETURNING *
                    """),
                    {
                        "name": site.name,
                        "topology": site.topology,
                        "description": site.description,
                        "site_id": site_id
                    }
                )
                await db.commit()
                return result.fetchone()

        result = await self.db.execute(
            text("""
                UPDATE sites 
                SET name = :name, topology = :topology, description = :description 
                WHERE id = :site_id 
                RETURNING *
            """),
            {
                "name": site.name,
                "topology": site.topology,
                "description": site.description,
                "site_id": site_id
            }
        )
        await self.db.commit()
        return result.fetchone()

    async def delete_site(self, site_id: int) -> bool:
        if not self.db:
            async with get_async_db() as db:
                # Remove associations
                await db.execute(
                    text("DELETE FROM site_coredevice_association WHERE site_id = :site_id"),
                    {"site_id": site_id}
                )

                # Delete site
                result = await db.execute(
                    text("DELETE FROM sites WHERE id = :site_id RETURNING id"),
                    {"site_id": site_id}
                )
                await db.commit()
                return result.rowcount > 0

        # Remove associations
        await self.db.execute(
            text("DELETE FROM site_coredevice_association WHERE site_id = :site_id"),
            {"site_id": site_id}
        )

        # Delete site
        result = await self.db.execute(
            text("DELETE FROM sites WHERE id = :site_id RETURNING id"),
            {"site_id": site_id}
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_links(self, site_id: int) -> List[Link]:
        if not self.db:
            async with get_async_db() as db:
                result = await db.execute(
                    text("SELECT * FROM links WHERE site_id = :site_id"),
                    {"site_id": site_id}
                )
                return result.fetchall()
        result = await self.db.execute(
            text("SELECT * FROM links WHERE site_id = :site_id"),
            {"site_id": site_id}
        )
        return result.fetchall()