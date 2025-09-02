from pydantic import BaseModel

class NetworkBase(BaseModel):
    name: str

class NetworkCreate(NetworkBase):
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)

class Network(NetworkBase):
    id: int

    class Config:
        # Replace 'orm_mode' with 'from_attributes'
        from_attributes = True