from typing import Optional
from pydantic import BaseModel

class LinkBase(BaseModel):
    name: Optional[str] = None
    physical_status: Optional[str] = None
    protocol_status: Optional[str] = None
    mpls_ldp: Optional[str] = None
    ospf: Optional[str] = None
    ospf_interface_address: Optional[str] = None
    bw: Optional[str] = None
    description: Optional[str] = None
    media_type: Optional[str] = None
    cdp: Optional[str] = None
    input_rate: Optional[str] = None
    output_rate: Optional[str] = None
    tx: Optional[str] = None
    rx: Optional[str] = None
    mtu: Optional[str] = None
    input_errors: Optional[str] = None
    output_errors: Optional[str] = None
    crc: Optional[str] = None
    interface_ip: Optional[str] = None  # Added schema field

class LinkCreate(LinkBase):
    pass

class Link(LinkBase):
    id: int

    class Config:
        # Replace 'orm_mode' with 'from_attributes'
        from_attributes = True
