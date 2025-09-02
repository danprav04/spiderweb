import json
import os
import pickle
import threading

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.core_device import CoreDevice
from app.models.crawler_cycle import CrawlerCycle
from app.models.link import Link
from app.models.site import Site
from app.repositories.coredevice_repository import CoreDeviceRepository
from app.repositories.crawler_cycle_repository import CrawlerCycleRepository
from app.schemas.link import LinkCreate, LinkBase
from sqlalchemy.exc import IntegrityError

from network.spectrum_topology import export_map

from app.models.alert import Alert
from sqlalchemy import and_
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload


class LinkRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db or next(get_async_db())
        self.coredevice_repository = CoreDeviceRepository(self.db)
        self.crawler_cycle_repository = CrawlerCycleRepository(self.db)
        self.cache_lock = threading.Lock()

    async def get_links(
            self, skip: int = 0, limit: int = 20,
            coredevice_id: int = None,
            neighbor_site_id: str = None,
            neighbor_coredevice_id: str = None,
            filters: LinkBase = None,
            start_date: datetime = None,
            end_date: datetime = None,
            crawler_cycle: int = None
    ):
        from sqlalchemy.orm import selectinload

        stmt = select(Link).options(
            selectinload(Link.coredevice),
            selectinload(Link.neighbor_site),
            selectinload(Link.neighbor_coredevice)
        )

        if coredevice_id is not None:
            stmt = stmt.filter(Link.coredevice_id == coredevice_id)

        if neighbor_site_id is not None:
            if neighbor_site_id == '*':
                stmt = stmt.filter(Link.neighbor_site_id != None)
            else:
                stmt = stmt.filter(Link.neighbor_site_id == int(neighbor_site_id))

        if neighbor_coredevice_id is not None:
            if neighbor_coredevice_id == '*':
                stmt = stmt.filter(Link.neighbor_coredevice_id != None)
            else:
                stmt = stmt.filter(Link.neighbor_coredevice_id == int(neighbor_coredevice_id))

        if filters:
            for field, value in filters.dict(exclude_none=True).items():
                column = getattr(Link, field, None)
                if column is not None:
                    if value.startswith('!'):
                        # Exclude rows that contain the string after the '!'
                        stmt = stmt.filter(column.notilike(f"%{value[1:]}%"))
                    else:
                        # Include rows that contain the string
                        stmt = stmt.filter(column.ilike(f"%{value}%"))

        if start_date and end_date:
            stmt = stmt.filter(Link.created_at >= start_date).filter(Link.created_at <= end_date)
        elif start_date:
            stmt = stmt.filter(Link.created_at >= start_date)
        elif end_date:
            stmt = stmt.filter(Link.created_at <= end_date)

        if crawler_cycle is not None:
            stmt = stmt.filter(Link.crawler_cycle == crawler_cycle)

        stmt = stmt.order_by(Link.id.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_links_with_neighbors(self) -> list:
        cache_file_path = os.path.join(os.getcwd(), 'links_with_neighbors_cache.pkl')

        stmt = select(CrawlerCycle).order_by(CrawlerCycle.count.desc()).limit(1)
        result = await self.db.execute(stmt)
        last_crawl_obj = result.scalar_one_or_none()
        if not last_crawl_obj:
            return []

        last_crawl = last_crawl_obj.count

        # Check cache
        with self.cache_lock:
            if os.path.exists(cache_file_path):
                try:
                    with open(cache_file_path, 'rb') as cache_file:
                        cached_data = pickle.load(cache_file)
                        if cached_data['last_crawl'] == last_crawl:
                            return cached_data['result']
                except Exception:
                    pass  # Fall through to regenerate data

        # Query with eager loading
        stmt = select(Link).options(
            joinedload(Link.coredevice),
            joinedload(Link.neighbor_site),
            joinedload(Link.neighbor_coredevice)
        ).filter(
            (Link.neighbor_coredevice_id != None) | (Link.neighbor_site_id != None)
        ).order_by(Link.name, Link.coredevice_id, Link.crawler_cycle.desc())

        result = await self.db.execute(stmt)
        most_recent_links_with_neighbors = result.scalars().all()

        # Deduplicate by (name, coredevice_id), keep latest
        seen_links = {}
        for link in most_recent_links_with_neighbors:
            key = (link.name, link.coredevice_id)
            if key not in seen_links or link.crawler_cycle > seen_links[key].crawler_cycle:
                seen_links[key] = link
        unique_most_recent_links_with_neighbors = list(seen_links.values())

        # Filter links for the latest crawl cycle
        stmt = select(Link).filter(Link.crawler_cycle == last_crawl)
        result = await self.db.execute(stmt)
        last_crawl_links = {f"{l.coredevice_id}_{l.name}": l for l in result.scalars().all()}

        result_list = []
        for nei_link in unique_most_recent_links_with_neighbors:
            key = f"{nei_link.coredevice_id}_{nei_link.name}"
            link = last_crawl_links.get(key)
            if not link:
                continue

            link_dict = {
                "id": link.id,
                "coredevice": link.coredevice.to_dict() if link.coredevice else None,
                "neighbor_site": nei_link.neighbor_site.to_dict() if nei_link.neighbor_site else None,
                "neighbor_coredevice": nei_link.neighbor_coredevice.to_dict() if nei_link.neighbor_coredevice else None,
                "neighbor_ip": link.neighbor_ip,
                "name": link.name,
                "physical_status": link.physical_status,
                "protocol_status": link.protocol_status,
                "mpls_ldp": link.mpls_ldp,
                "ospf": link.ospf,
                "ospf_interface_address": link.ospf_interface_address,
                "bw": link.bw,
                "description": link.description,
                "media_type": link.media_type,
                "cdp": link.cdp,
                "input_rate": link.input_rate,
                "output_rate": link.output_rate,
                "tx": link.tx,
                "rx": link.rx,
                "mtu": link.mtu,
                "input_errors": link.input_errors,
                "output_errors": link.output_errors,
                "crc": link.crc,
                "interface_ip": link.interface_ip,
                "created_at": link.created_at,
                "crawler_cycle": link.crawler_cycle,
                "neighbor_data_crawl": nei_link.crawler_cycle
            }
            result_list.append(link_dict)

        # Cache the result
        with self.cache_lock:
            cached_data = {
                'last_crawl': last_crawl,
                'result': result_list,
                'timestamp': datetime.now().timestamp()
            }
            with open(cache_file_path, 'wb') as cache_file:
                pickle.dump(cached_data, cache_file)

        return result_list

    async def get_links_to_end_sites(self, coredevice_id: int = None):
        stmt = select(CrawlerCycle).order_by(CrawlerCycle.count.desc()).limit(1)
        result = await self.db.execute(stmt)
        last_crawler_cycle = result.scalar_one_or_none()
        if last_crawler_cycle is None:
            return []

        stmt = select(Link).filter(Link.crawler_cycle == last_crawler_cycle.count)

        if coredevice_id is not None:
            stmt = stmt.filter(Link.coredevice_id == coredevice_id)

        # Ensure neighbor_site_id is not None (any value is acceptable)
        stmt = stmt.filter(Link.neighbor_site_id != None)

        # Ensure neighbor_coredevice_id is None
        stmt = stmt.filter(Link.neighbor_coredevice_id == None)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_link(self, link_id: int):
        stmt = select(Link).filter(Link.id == link_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_link(self, link: LinkCreate, coredevice_id: int, count: int, neighbor_coredevice_id: int = None,
                          container_name: str = None, neighbor_ip: str = None):
        stmt = select(CoreDevice).filter(CoreDevice.id == coredevice_id)
        result = await self.db.execute(stmt)
        db_coredevice = result.scalar_one_or_none()

        neighbor_coredevice = None
        if neighbor_coredevice_id:
            stmt = select(CoreDevice).filter(CoreDevice.id == neighbor_coredevice_id)
            result = await self.db.execute(stmt)
            neighbor_coredevice = result.scalar_one_or_none()

        db_site = None
        if container_name:
            # Check if a site with the same container name already exists
            stmt = select(Site).filter(Site.name == container_name)
            result = await self.db.execute(stmt)
            db_site = result.scalar_one_or_none()
            if not db_site:
                # If not, create a new site
                try:
                    db_site = Site(name=container_name, topology='', description="")
                    self.db.add(db_site)
                    await self.db.commit()
                    await self.db.refresh(db_site)
                except IntegrityError:
                    # If a site with the same name already exists, do nothing
                    await self.db.rollback()

        if db_coredevice and db_site:
            # Check if the site is already attached to a core device
            stmt = text(
                "SELECT * FROM site_coredevice_association WHERE site_id = :site_id AND coredevice_id = :coredevice_id"
            )
            result = await self.db.execute(stmt, {"site_id": db_site.id, "coredevice_id": db_coredevice.id})
            existing_association = result.fetchone()
            if not existing_association:
                # If not, add the core device to the site's core devices manually
                stmt = text(
                    "INSERT INTO site_coredevice_association (site_id, coredevice_id) VALUES (:site_id, :coredevice_id)"
                )
                await self.db.execute(stmt, {"site_id": db_site.id, "coredevice_id": db_coredevice.id})
                await self.db.commit()

            db_link = Link(
                name=link.name,
                physical_status=link.physical_status,
                protocol_status=link.protocol_status,
                mpls_ldp=link.mpls_ldp,
                ospf=link.ospf,
                ospf_interface_address=link.ospf_interface_address,
                bw=link.bw,
                description=link.description,
                media_type=link.media_type,
                cdp=link.cdp,
                input_rate=link.input_rate,
                output_rate=link.output_rate,
                tx=link.tx,
                rx=link.rx,
                mtu=link.mtu,
                input_errors=link.input_errors,
                output_errors=link.output_errors,
                crc=link.crc,
                interface_ip=link.interface_ip,
                coredevice=db_coredevice,
                neighbor_coredevice=neighbor_coredevice or None,
                neighbor_site=db_site or None,
                neighbor_ip=neighbor_ip or None,
                crawler_cycle=count
            )
            self.db.add(db_link)
            try:
                await self.db.commit()
                await self.db.refresh(db_link)
                return db_link
            except IntegrityError:
                await self.db.rollback()
        elif db_coredevice:
            db_link = Link(
                name=link.name,
                physical_status=link.physical_status,
                protocol_status=link.protocol_status,
                mpls_ldp=link.mpls_ldp,
                ospf=link.ospf,
                ospf_interface_address=link.ospf_interface_address,
                bw=link.bw,
                description=link.description,
                media_type=link.media_type,
                cdp=link.cdp,
                input_rate=link.input_rate,
                output_rate=link.output_rate,
                tx=link.tx,
                rx=link.rx,
                mtu=link.mtu,
                input_errors=link.input_errors,
                output_errors=link.output_errors,
                crc=link.crc,
                interface_ip=link.interface_ip,
                coredevice=db_coredevice,
                neighbor_coredevice=neighbor_coredevice or None,
                neighbor_site=None,
                neighbor_ip=neighbor_ip or None,
                crawler_cycle=count
            )
            self.db.add(db_link)
            try:
                await self.db.commit()
                await self.db.refresh(db_link)
                return db_link
            except IntegrityError:
                await self.db.rollback()
        return None

    async def update_link(self, link_id: int, link: LinkCreate, site_id: int):
        stmt = select(Link).filter(Link.id == link_id)
        result = await self.db.execute(stmt)
        db_link = result.scalar_one_or_none()

        stmt = select(Site).filter(Site.id == site_id)
        result = await self.db.execute(stmt)
        db_site = result.scalar_one_or_none()

        if db_link and db_site:
            db_link.name = link.name
            db_link.physical_status = link.physical_status
            db_link.protocol_status = link.protocol_status
            db_link.mpls_ldp = link.mpls_ldp
            db_link.ospf = link.ospf
            db_link.bw = link.bw
            db_link.description = link.description
            db_link.media_type = link.media_type
            db_link.cdp = link.cdp
            db_link.input_rate = link.input_rate
            db_link.rx = link.rx
            db_link.mtu = link.mtu
            db_link.interface_address = link.interface_address
            db_link.site = db_site
            try:
                await self.db.commit()
                await self.db.refresh(db_link)
                return db_link
            except IntegrityError:
                await self.db.rollback()
        return None

    async def delete_link(self, link_id: int):
        stmt = select(Link).filter(Link.id == link_id)
        result = await self.db.execute(stmt)
        db_link = result.scalar_one_or_none()
        if db_link:
            self.db.delete(db_link)
            try:
                await self.db.commit()
                return True
            except IntegrityError:
                await self.db.rollback()
        return False

    async def add_link_to_user(self, user_id: int, link_id: int):
        stmt = select(User).filter(User.id == user_id)
        result = await self.db.execute(stmt)
        db_user = result.scalar_one_or_none()

        stmt = select(Link).filter(Link.id == link_id)
        result = await self.db.execute(stmt)
        db_link = result.scalar_one_or_none()

        if db_user and db_link:
            db_user.links.append(db_link)
            try:
                await self.db.commit()
                return True
            except IntegrityError:
                await self.db.rollback()
        return False

    async def remove_link_from_user(self, user_id: int, link_id: int):
        stmt = select(User).filter(User.id == user_id)
        result = await self.db.execute(stmt)
        db_user = result.scalar_one_or_none()

        stmt = select(Link).filter(Link.id == link_id)
        result = await self.db.execute(stmt)
        db_link = result.scalar_one_or_none()

        if db_user and db_link:
            db_user.links.remove(db_link)
            try:
                await self.db.commit()
                return True
            except IntegrityError:
                await self.db.rollback()
        return False

    async def process_links(self):
        """
        Fetch data, sort and create links, and save them to the database.
        """
        await self.fetch_data()
        await self.sort_and_create_links()
        await self.save_to_database()