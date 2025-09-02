from typing import Dict

from sqlalchemy import Integer, String, Column, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from typing_extensions import Any

from . import Base

# Association table for Site and CoreDevice
site_coredevice_association = Table(
    "site_coredevice_association",
    Base.metadata,
    Column("site_id", Integer, ForeignKey("sites.id"), primary_key=True),
    Column("coredevice_id", Integer, ForeignKey("coredevices.id"), primary_key=True),
)

class Site(Base):
    """
    Site model
    """
    __tablename__ = "sites"
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=False, unique=True)
    topology: str = Column(String, nullable=True)
    description: str = Column(String, nullable=True)
    coredevices: Mapped["CoreDevice"] = relationship(
        "CoreDevice", secondary=site_coredevice_association, back_populates="sites"
    )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "topology": self.topology,
            "description": self.description,
        }
        return result

    def __repr__(self):
        return f"Site(name='{self.name}')"
