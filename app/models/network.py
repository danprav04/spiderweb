from dataclasses import dataclass
from typing import Dict, Any
from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from . import Base

class Network(Base):
    """
    Network model
    """
    __tablename__ = "networks"
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=False, unique=True)
    core_sites: Mapped["CoreSite"] = relationship(
        "CoreSite", secondary="core_site_network_association", back_populates="networks", uselist=True
    )
    core_devices: Mapped["CoreDevice"] = relationship(
        "CoreDevice", secondary="core_device_network_association", back_populates="networks", uselist=True
    )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
        }
        return result

    def __repr__(self):
        return f"Network(name='{self.name}')"
