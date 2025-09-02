from pydantic import BaseModel
from enum import Enum

class Role(str, Enum):
    admin = "admin"
    user = "user"

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    role: Role = "user"

class User(UserBase):
    id: int
    role: Role

    class Config:
        # Replace 'orm_mode' with 'from_attributes'
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str
