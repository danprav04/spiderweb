from app.database import get_db
from app.models.alert import Alert
from app.models.core_device import CoreDevice
from app.models.crawler_cycle import CrawlerCycle
from app.models.link import Link
from app.repositories.link_repository import LinkRepository
from crawler import LinkService
from crawler.sync_repos.sync_coredevice_repo import CoreDeviceRepository
from crawler.sync_repos.sync_crawler_cycle_repo import CrawlerCycleRepository
from concurrent.futures import ProcessPoolExecutor
from time import time

from crawler.create_alerts import create_alerts
from network.spectrum_container import get_spectrum_container_data
from network.trino_getip import create_connection_instance, get_all_int_ips


def crawl_core_device(ip, username, password, coredevice_id, core_devices, int_ips, spectrum_container_data, count):
    try:
        link_service = LinkService(ip, username, password, coredevice_id, core_devices, int_ips,
                                   spectrum_container_data, count)
        link_service.process_links()
        print(f"Crawler finished for core device with IP {ip}")
    except Exception as e:
        print(f"Error occurred for core device with IP {ip}: {str(e)}")


def main():
    core_device_repo = CoreDeviceRepository()
    core_devices = core_device_repo.get_coredevices()
    db = create_connection_instance()

    int_ips = get_all_int_ips(db)
    spectrum_container_data = get_spectrum_container_data()

    crawler_cycle_repo = CrawlerCycleRepository()
    crawler_cycle = crawler_cycle_repo.get_crawler_cycle()

    # Handle case where no crawler cycle exists
    if crawler_cycle is None:
        print("No crawler cycle found. Creating one with count = 0.")
        # Create a new cycle with count 0
        new_cycle = CrawlerCycle(count=0)
        crawler_cycle_repo.db.add(new_cycle)
        crawler_cycle_repo.db.commit()
        crawler_cycle = new_cycle

    count = crawler_cycle.count

    with ProcessPoolExecutor(max_workers=10) as executor:
        futures = []
        for core_device in core_devices:
            future = executor.submit(crawl_core_device, core_device.ip, '{username}', "{password}",
                                     core_device.id, core_devices, int_ips, spectrum_container_data, count + 1)
            futures.append(future)

        for future in futures:
            future.result()

    create_alerts(next(get_db()))

    crawler_cycle_repo.increment_crawler_cycle()
    crawler_cycle = crawler_cycle_repo.get_crawler_cycle()
    count = crawler_cycle.count

    print(f"Crawler cycle count: {count}")


if __name__ == "__main__":
    start_time = time()

    main()

    duration = time() - start_time
    print(f"\n\nCrawler cycle duration: {round(duration)} seconds")