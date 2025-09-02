from typing import Optional, List

from fastapi import Depends
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.link import Link
from app.models.user import User
from app.schemas.user import UserCreate
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import jwt
from app.config import Config


class UserRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db or next(get_async_db())

    async def get_users(self):
        stmt = select(User)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user(self, user_id: int):
        stmt = select(User).filter(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str):
        stmt = select(User).filter(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user: UserCreate):
        try:
            db_user = User(username=user.username, role=user.role)
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)

            # Create a JWT payload with the user's username and role
            payload = {
                'username': db_user.username,
                'role': db_user.role,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }

            # Generate a JWT token
            token = jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

            return {'token': token, 'user': db_user}
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update_user(self, user_id: int, user: UserCreate):
        try:
            stmt = select(User).filter(User.id == user_id)
            result = await self.db.execute(stmt)
            db_user = result.scalar_one_or_none()

            if db_user:
                db_user.username = user.username
                db_user.role = user.role
                await self.db.commit()
                await self.db.refresh(db_user)

                # Create a JWT payload with the updated user's username and role
                payload = {
                    'username': db_user.username,
                    'role': db_user.role,
                    'exp': datetime.utcnow() + timedelta(minutes=30)
                }

                # Generate a JWT token
                token = jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

                return {'token': token, 'user': db_user}
            return None
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_user(self, user_id: int):
        try:
            stmt = select(User).filter(User.id == user_id)
            result = await self.db.execute(stmt)
            db_user = result.scalar_one_or_none()

            if db_user:
                await self.db.delete(db_user)
                await self.db.commit()
                return True
            return False
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_user_links(self, user_id: int) -> Optional[List[Link]]:
        stmt = select(User).filter(User.id == user_id)
        result = await self.db.execute(stmt)
        db_user = result.scalar_one_or_none()

        if db_user:
            # Fetch links from the user_link table
            links = await self.db.execute(text(
                "SELECT l.* FROM links l JOIN user_link ul ON l.id = ul.link_id WHERE ul.user_id = :user_id"),
                {"user_id": db_user.id})

            # Convert the Row objects to dictionaries
            link_dicts = [dict(link._asdict()) for link in links.fetchall()]

            # Create Link objects from the dictionaries
            return [Link(**link_dict) for link_dict in link_dicts]
        return None

    async def add_link_to_user(self, user_id: int, link_id: int):
        stmt_user = select(User).filter(User.id == user_id)
        result_user = await self.db.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        stmt_link = select(Link).filter(Link.id == link_id)
        result_link = await self.db.execute(stmt_link)
        db_link = result_link.scalar_one_or_none()

        if db_user and db_link:
            # Check if the link is already added to the user's favorite links
            existing_association = await self.db.execute(text(
                "SELECT * FROM user_link WHERE user_id = :user_id AND link_id = :link_id"),
                {"user_id": db_user.id, "link_id": db_link.id})

            if not existing_association.fetchone():
                # If not, add the link to the user's favorite links manually
                await self.db.execute(text(
                    "INSERT INTO user_link (user_id, link_id) VALUES (:user_id, :link_id)"),
                    {"user_id": db_user.id, "link_id": db_link.id})
                await self.db.commit()
                return True
        return False

    async def remove_link_from_user(self, user_id: int, link_id: int):
        stmt_user = select(User).filter(User.id == user_id)
        result_user = await self.db.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        stmt_link = select(Link).filter(Link.id == link_id)
        result_link = await self.db.execute(stmt_link)
        db_link = result_link.scalar_one_or_none()

        if db_user and db_link:
            # Check if the link is already added to the user's favorite links
            existing_association = await self.db.execute(text(
                "SELECT * FROM user_link WHERE user_id = :user_id AND link_id = :link_id"),
                {"user_id": db_user.id, "link_id": db_link.id})

            if existing_association.fetchone():
                # If it is, remove the link from the user's favorite links manually
                await self.db.execute(text(
                    "DELETE FROM user_link WHERE user_id = :user_id AND link_id = :link_id"),
                    {"user_id": db_user.id, "link_id": db_link.id})
                await self.db.commit()
                return True
        return False