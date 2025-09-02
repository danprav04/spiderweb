from pydantic import BaseModel

class SiteBase(BaseModel):
    name: str
    topology: str
    description: str

class SiteCreate(SiteBase):
    pass

class Site(SiteBase):
    id: int

    class Config:
        # Replace 'orm_mode' with 'from_attributes'
        from_attributes = True

class SiteDescription(BaseModel):
    description: str
