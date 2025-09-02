from dataclasses import dataclass
from typing import Dict, Any
from sqlalchemy import Integer, String, Column, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from . import Base

# Association table for CoreSite and Network
core_site_network_association = Table(
    "core_site_network_association",
    Base.metadata,
    Column("core_site_id", Integer, ForeignKey("coresites.id"), primary_key=True),
    Column("network_id", Integer, ForeignKey("networks.id"), primary_key=True),
)

class CoreSite(Base):
    """
    CoreSite model
    """
    __tablename__ = "coresites"
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=False, unique=True)
    networks: Mapped["Network"] = relationship(
        "Network", secondary=core_site_network_association, back_populates="core_sites", uselist=True
    )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
        }
        return result

    def __repr__(self):
        return f"CoreSite(name='{self.name}')"
