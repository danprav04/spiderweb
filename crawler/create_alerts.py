from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.core_device import CoreDevice
from app.models.crawler_cycle import CrawlerCycle
from app.models.link import Link
from crawler.config import physical_status_severity, protocol_status_severity, mpls_ldp_severity, ospf_severity, \
    physical_status_type, protocol_status_type, mpls_ldp_type, ospf_type


def identify_alert_changes(changes, link, second_last_link):

    for column in ["physical_status", "protocol_status", "mpls_ldp", "ospf"]:
        new = getattr(link, column)
        old = getattr(second_last_link, column)
        if old != new:

            severity_score = 0
            alert_type = "info"
            if column == "physical_status":
                if new.lower() != "up":
                    severity_score = max(severity_score, int(physical_status_severity))
                    alert_type = physical_status_type
            elif column == "protocol_status":
                if new.lower() != "up":
                    severity_score = max(severity_score, int(protocol_status_severity))
                    alert_type = protocol_status_type
            elif column == "mpls_ldp":
                if new.lower() != "up":
                    severity_score = max(severity_score, int(mpls_ldp_severity))
                    alert_type = mpls_ldp_type
            elif column == "ospf":
                if new.lower() != "full":
                    severity_score = max(severity_score, int(ospf_severity))
                    alert_type = ospf_type

            changes.append({
                "old_value": old,
                "new_value": new,
                "alert_type": alert_type,
                "severity_score": severity_score,
                "description": f"{column.capitalize().replace('_', ' ')} changed from '{old}' to '{new}'"
            })


def _create_alerts(db: Session, last_crawler_cycle, second_last_crawler_cycle):

    if last_crawler_cycle and second_last_crawler_cycle:
        # Get the links from the last two crawler cycles
        last_links = db.query(Link).filter(Link.crawler_cycle == last_crawler_cycle).all()
        second_last_links = db.query(Link).filter(Link.crawler_cycle == second_last_crawler_cycle).all()

        # Create a dictionary to store the links from the second last crawler cycle
        second_last_links_dict = {(link.coredevice_id, link.name): link for link in second_last_links}

        # Iterate over the links from the last crawler cycle
        for link in last_links:
            # Get the corresponding link from the second last crawler cycle
            second_last_link = second_last_links_dict.get((link.coredevice_id, link.name))

            # If the link exists in both crawler cycles
            if second_last_link:
                # Compare the states of every column
                changes = []

                identify_alert_changes(changes, link, second_last_link)

                for change in changes:
                    db_coredevice = db.query(CoreDevice).filter(CoreDevice.id == link.coredevice_id).first()
                    coredevice_name = db_coredevice.name if db_coredevice else "Unknown"
                    message = f"Link {link.name} on core device {coredevice_name} has changed: {change['description']}"
                    alert = Alert(
                        type=change['alert_type'],
                        message=message,
                        network_line=link.name,
                        source="crawler",
                        severity_score=change['severity_score'],
                        details=changes,
                        crawl_number=last_crawler_cycle,
                        coredevice_name=coredevice_name,
                        coredevice_id=link.coredevice_id
                    )
                    db.add(alert)
                    db.commit()


def create_alerts(db: Session):
    # Get the last two crawler cycles
    last_crawler_cycle = db.query(CrawlerCycle).order_by(CrawlerCycle.count.desc()).first().count
    second_last_crawler_cycle = last_crawler_cycle - 1
    _create_alerts(db, last_crawler_cycle, second_last_crawler_cycle)


if __name__ == '__main__':
    _create_alerts(db=next(get_db()), last_crawler_cycle=10, second_last_crawler_cycle=9)
