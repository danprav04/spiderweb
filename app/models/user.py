from sqlalchemy import Integer, String, Column, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped
from . import Base

user_link_table = Table(
    'user_link',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('link_id', Integer, ForeignKey('links.id'))
)

class User(Base):
    """
    User model
    """
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True)
    username: str = Column(String, nullable=False, unique=True)
    role: str = Column(String, nullable=False, default="user")
    links: Mapped["Link"] = relationship("Link", secondary="user_link", back_populates="users", lazy="selectin")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role
        }

    def __repr__(self):
        return f"User(username='{self.username}', role='{self.role}')"