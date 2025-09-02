import json
import os
import pickle
import threading

from sqlalchemy import text

from app.database import get_db
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


class LinkRepository:
    def __init__(self, db=None):
        self.db = db or next(get_db())
        self.coredevice_repository = CoreDeviceRepository(self.db)
        self.crawler_cycle_repository = CrawlerCycleRepository(self.db)
        self.cache_lock = threading.Lock()

    def get_links(self, skip: int = 0, limit: int = 20, coredevice_id: int = None,
                  neighbor_site_id: str = None, neighbor_coredevice_id: str = None,
                  filters: LinkBase = None, start_date: datetime = None, end_date: datetime = None,
                  crawler_cycle: int = None):
        query = self.db.query(Link)

        if coredevice_id is not None:
            query = query.filter(Link.coredevice_id == coredevice_id)

        if neighbor_site_id is not None:
            if neighbor_site_id == '*':
                query = query.filter(Link.neighbor_site_id != None)
            else:
                query = query.filter(Link.neighbor_site_id == int(neighbor_site_id))

        if neighbor_coredevice_id is not None:
            if neighbor_coredevice_id == '*':
                query = query.filter(Link.neighbor_coredevice_id != None)
            else:
                query = query.filter(Link.neighbor_coredevice_id == int(neighbor_coredevice_id))

        if filters:
            for field, value in filters.dict(exclude_none=True).items():
                column = getattr(Link, field, None)
                if column is not None:
                    if value.startswith('!'):
                        # Exclude rows that contain the string after the '!'
                        query = query.filter(column.notilike(f"%{value[1:]}%"))
                    else:
                        # Include rows that contain the string
                        query = query.filter(column.ilike(f"%{value}%"))

        if start_date and end_date:
            query = query.filter(Link.created_at >= start_date).filter(Link.created_at <= end_date)
        elif start_date:
            query = query.filter(Link.created_at >= start_date)
        elif end_date:
            query = query.filter(Link.created_at <= end_date)

        if crawler_cycle is not None:
            query = query.filter(Link.crawler_cycle == crawler_cycle)

        return query.order_by(Link.id.desc()).offset(skip).limit(limit).all()

    def get_links_with_neighbors(self):
        # Define the cache file path
        cache_file_path = os.path.join(os.getcwd(), 'links_with_neighbors_cache.pkl')

        # Get the last crawl number
        last_crawl = self.db.query(CrawlerCycle).first().count

        # Check if the cache file exists and is up-to-date
        with self.cache_lock:
            if os.path.exists(cache_file_path):
                with open(cache_file_path, 'rb') as cache_file:
                    cached_data = pickle.load(cache_file)
                    if cached_data['last_crawl'] == last_crawl:
                        # Return the cached data
                        return cached_data['result']

        # Get all links with neighbors from any crawl cycle, with only the most recent entry per link
        most_recent_links_with_neighbors = self.db.query(Link).filter(
            (Link.neighbor_coredevice_id != None) | (Link.neighbor_site_id != None)
        ).order_by(Link.name, Link.coredevice_id, Link.crawler_cycle.desc()).all()

        # Remove duplicate links, keeping only the most recent one
        seen_links = set()
        unique_most_recent_links_with_neighbors = []
        for link in most_recent_links_with_neighbors:
            key = (link.name, link.coredevice_id)
            if key not in seen_links:
                unique_most_recent_links_with_neighbors.append(link)
                seen_links.add(key)

        last_crawl_links = self.db.query(Link).filter((Link.crawler_cycle == last_crawl)).all()
        result = []
        for nei_link in unique_most_recent_links_with_neighbors:
            link = next(
                (l for l in last_crawl_links if l.coredevice_id == nei_link.coredevice_id and l.name == nei_link.name),
                None)

            link_dict = {
                "id": link.id,
                "coredevice": link.coredevice.to_dict() if link.coredevice else None,
                "neighbor_site": nei_link.neighbor_site.to_dict() if link.neighbor_site else None,
                "neighbor_coredevice": nei_link.neighbor_coredevice.to_dict() if link.neighbor_coredevice else None,
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
                "interface_ip": link.interface_ip,  # Added to dict
                "created_at": link.created_at,
                "crawler_cycle": link.crawler_cycle,
                "neighbor_data_crawl": nei_link.crawler_cycle
            }

            result.append(link_dict)

        # Cache the result
        with self.cache_lock:
            cached_data = {
                'last_crawl': last_crawl,
                'result': result,
                'timestamp': datetime.now().timestamp()
            }
            with open(cache_file_path, 'wb') as cache_file:
                pickle.dump(cached_data, cache_file)

        return result

    def get_links_to_end_sites(self, coredevice_id: int = None):
        last_crawler_cycle = link_repo.db.query(CrawlerCycle).order_by(CrawlerCycle.count.desc()).first()
        if last_crawler_cycle is None:
            return []

        query = link_repo.db.query(Link).filter(Link.crawler_cycle == last_crawler_cycle.count)

        if coredevice_id is not None:
            query = query.filter(Link.coredevice_id == coredevice_id)

        # Ensure neighbor_site_id is not None (any value is acceptable)
        query = query.filter(Link.neighbor_site_id != None)

        # Ensure neighbor_coredevice_id is None
        query = query.filter(Link.neighbor_coredevice_id == None)

        return query.all()

    def get_link(self, link_id: int):
        return self.db.query(Link).filter(Link.id == link_id).first()

    def create_link(self, link: LinkCreate, coredevice_id: int, count: int, neighbor_coredevice_id: int = None,
                    container_name: str = None, neighbor_ip: str = None):
        db_coredevice = self.db.query(CoreDevice).filter(CoreDevice.id == coredevice_id).first()

        neighbor_coredevice = None
        if neighbor_coredevice_id:
            neighbor_coredevice = self.db.query(CoreDevice).filter(CoreDevice.id == neighbor_coredevice_id).first()

        db_site = None
        if container_name:
            # Check if a site with the same container name already exists
            db_site = self.db.query(Site).filter(Site.name == container_name).first()
            if not db_site:
                # If not, create a new site
                try:
                    db_site = Site(name=container_name, topology='', description="")
                    self.db.add(db_site)
                    self.db.commit()
                    self.db.refresh(db_site)
                except IntegrityError:
                    # If a site with the same name already exists, do nothing
                    self.db.rollback()

        if db_coredevice and db_site:
            # Check if the site is already attached to a core device
            existing_association = self.db.execute(text(
                "SELECT * FROM site_coredevice_association WHERE site_id = :site_id AND coredevice_id = :coredevice_id"),
                {"site_id": db_site.id, "coredevice_id": db_coredevice.id}).first()
            if not existing_association:
                # If not, add the core device to the site's core devices manually
                self.db.execute(text(
                    "INSERT INTO site_coredevice_association (site_id, coredevice_id) VALUES (:site_id, :coredevice_id)"),
                    {"site_id": db_site.id, "coredevice_id": db_coredevice.id})
                self.db.commit()

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
                interface_ip=link.interface_ip,  # Added interface_ip
                coredevice=db_coredevice,
                neighbor_coredevice=neighbor_coredevice or None,
                neighbor_site=db_site or None,
                neighbor_ip=neighbor_ip or None,
                crawler_cycle=count  # Save the count to the crawler cycle
            )
            self.db.add(db_link)
            try:
                self.db.commit()
                self.db.refresh(db_link)
                return db_link
            except IntegrityError:
                self.db.rollback()
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
                interface_ip=link.interface_ip,  # Added interface_ip
                coredevice=db_coredevice,
                neighbor_coredevice=neighbor_coredevice or None,
                neighbor_site=None,
                neighbor_ip=neighbor_ip or None,
                crawler_cycle=count  # Save the count to the crawler cycle
            )
            self.db.add(db_link)
            try:
                self.db.commit()
                self.db.refresh(db_link)
                return db_link
            except IntegrityError:
                self.db.rollback()
        return None

    def update_link(self, link_id: int, link: LinkCreate, site_id: int):
        db_link = self.db.query(Link).filter(Link.id == link_id).first()
        db_site = self.db.query(Site).filter(Site.id == site_id).first()
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
                self.db.commit()
                self.db.refresh(db_link)
                return db_link
            except IntegrityError:
                self.db.rollback()
        return None

    def delete_link(self, link_id: int):
        db_link = self.db.query(Link).filter(Link.id == link_id).first()
        if db_link:
            self.db.delete(db_link)
            try:
                self.db.commit()
                return True
            except IntegrityError:
                self.db.rollback()
        return False

    def add_link_to_user(self, user_id: int, link_id: int):
        db_user = self.db.query(User).filter(User.id == user_id).first()
        db_link = self.db.query(Link).filter(Link.id == link_id).first()
        if db_user and db_link:
            db_user.links.append(db_link)
            try:
                self.db.commit()
                return True
            except IntegrityError:
                self.db.rollback()
        return False

    def remove_link_from_user(self, user_id: int, link_id: int):
        db_user = self.db.query(User).filter(User.id == user_id).first()
        db_link = self.db.query(Link).filter(Link.id == link_id).first()
        if db_user and db_link:
            db_user.links.remove(db_link)
            try:
                self.db.commit()
                return True
            except IntegrityError:
                self.db.rollback()
        return False

    def process_links(self):
        """
        Fetch data, sort and create links, and save them to the database.
        """
        self.fetch_data()
        self.sort_and_create_links()
        self.save_to_database()
