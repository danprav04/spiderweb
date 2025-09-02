from . import Base
from typing import Dict
from sqlalchemy import Integer, String, Column, ForeignKey, Table, DateTime
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import JSONB
from typing_extensions import Any
import json

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    network_line = Column(String)
    source = Column(String)
    severity_score = Column(Integer)
    details = Column(JSONB)
    crawl_number = Column(Integer)
    coredevice_name = Column(String)
    coredevice_id = Column(Integer)

    def to_dict(self):
        # Convert datetime object to a string that can be serialized to JSON
        return {
            "id": self.id,
            "type": self.type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),  # Convert to ISO format string
            "network_line": self.network_line,
            "source": self.source,
            "severity_score": self.severity_score,
            "details": self.details,
            "crawl_number": self.crawl_number,
            "coredevice_name": self.coredevice_name,
            "coredevice_id": self.coredevice_id
        }
