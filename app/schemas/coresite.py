from pydantic import BaseModel

class CoreSiteBase(BaseModel):
    name: str

class CoreSiteCreate(CoreSiteBase):
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)

class CoreSite(CoreSiteBase):
    id: int

    class Config:
        # Replace 'orm_mode' with 'from_attributes'
        from_attributes = True