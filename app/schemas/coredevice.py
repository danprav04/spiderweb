from pydantic import BaseModel

class CoreDeviceBase(BaseModel):
    name: str
    ip: str

class CoreDeviceCreate(CoreDeviceBase):
    def __init__(self, name: str, ip: str, **kwargs):
        super().__init__(name=name, ip=ip, **kwargs)

class CoreDevice(CoreDeviceBase):
    id: int

    class Config:
        # Replace 'orm_mode' with 'from_attributes'
        from_attributes = True