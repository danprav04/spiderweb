from typing import Dict, List

from sqlalchemy import Integer, String, Column, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from typing_extensions import Any

from . import Base

# Association table for CoreDevice and Network
core_device_network_association = Table(
    "core_device_network_association",
    Base.metadata,
    Column("core_device_id", Integer, ForeignKey("coredevices.id"), primary_key=True),
    Column("network_id", Integer, ForeignKey("networks.id"), primary_key=True),
)

class CoreDevice(Base):
    """
    CoreDevice model
    """
    __tablename__ = "coredevices"
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=False, unique=True)
    ip: str = Column(String, nullable=False, unique=True)
    coresite_id: int = Column(Integer, ForeignKey("coresites.id"), nullable=False)
    coresite: Mapped["CoreSite"] = relationship("CoreSite")
    networks: Mapped[List["Network"]] = relationship(
        "Network", secondary=core_device_network_association, back_populates="core_devices"
    )
    sites: Mapped[List["Site"]] = relationship(
        "Site", secondary="site_coredevice_association", back_populates="coredevices"
    )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "ip": self.ip,
            "coresite_id": self.coresite_id,
        }
        return result

    def __repr__(self):
        return f"CoreDevice(name='{self.name}', ip='{self.ip}')"
