from sqlalchemy import Integer, String, Column, ForeignKey, Table, DateTime, Enum
from sqlalchemy.orm import relationship, Mapped
from . import Base
from datetime import datetime

class Link(Base):
    """
    Link model
    """
    __tablename__ = "links"
    id: int = Column(Integer, primary_key=True)
    coredevice_id: int = Column(Integer, ForeignKey("coredevices.id"), nullable=False)
    neighbor_site_id: int = Column(Integer, ForeignKey("sites.id"), nullable=True)
    neighbor_coredevice_id: int = Column(Integer, ForeignKey("coredevices.id"), nullable=True)
    neighbor_ip: str = Column(String, nullable=True)
    name: str = Column(String, nullable=False, unique=False)
    interface_ip: str = Column(String, nullable=True)
    description: str = Column(String, nullable=True)
    cdp: str = Column(String, nullable=True)
    physical_status: str = Column(String, nullable=True)
    protocol_status: str = Column(String, nullable=True)
    mpls_ldp: str = Column(String, nullable=True)
    ospf: str = Column(String, nullable=True)
    ospf_interface_address: str = Column(String, nullable=True)
    bw: str = Column(String, nullable=True)
    media_type: str = Column(String, nullable=True)
    input_rate: str = Column(String, nullable=True)
    output_rate: str = Column(String, nullable=True)
    tx: str = Column(String, nullable=True)
    rx: str = Column(String, nullable=True)
    mtu: str = Column(String, nullable=True)
    input_errors: str = Column(String, nullable=True)
    output_errors: str = Column(String, nullable=True)
    crc: str = Column(String, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    crawler_cycle: int = Column(Integer, nullable=False, default=0)
    coredevice: Mapped["CoreDevice"] = relationship("CoreDevice", foreign_keys=[coredevice_id])
    neighbor_site: Mapped["Site"] = relationship("Site")
    neighbor_coredevice: Mapped["CoreDevice"] = relationship("CoreDevice", foreign_keys=[neighbor_coredevice_id])
    users: Mapped["User"] = relationship("User", secondary="user_link", back_populates="links")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "coredevice": self.coredevice.to_dict() if self.coredevice else None,
            "neighbor_site": self.neighbor_site.to_dict() if self.neighbor_site else None,
            "neighbor_coredevice": self.neighbor_coredevice.to_dict() if self.neighbor_coredevice else None,
            "neighbor_ip": self.neighbor_ip,
            "name": self.name,
            "physical_status": self.physical_status,
            "protocol_status": self.protocol_status,
            "mpls_ldp": self.mpls_ldp,
            "ospf": self.ospf,
            "ospf_interface_address": self.ospf_interface_address,
            "bw": self.bw,
            "description": self.description,
            "media_type": self.media_type,
            "cdp": self.cdp,
            "input_rate": self.input_rate,
            "output_rate": self.output_rate,
            "tx": self.tx,
            "rx": self.rx,
            "mtu": self.mtu,
            "input_errors": self.input_errors,
            "output_errors": self.output_errors,
            "crc": self.crc,
            "interface_ip": self.interface_ip,  # Added to dict
            "created_at": self.created_at,
            "crawler_cycle": self.crawler_cycle
        }
        return result

    def __repr__(self):
        return f"Link(name='{self.name}')"
