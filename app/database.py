from dataclasses import dataclass
from typing import Dict, Any

from fastapi import FastAPI
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.config import Config
from alembic import config, command
from alembic.runtime import migration

from app.models.core_site import CoreSite
from app.models.core_device import CoreDevice
from app.models.link import Link
from app.models.network import Network
from app.models.site import Site
from app.models.user import User
from app.models.crawler_cycle import CrawlerCycle
from app.models.alert import Alert
from app.models import Base

# Create a database engine
SQLALCHEMY_DATABASE_URL = Config.DATABASE_URL
SYNC_DATABASE_URL = Config.SYNC_DATABASE_URL

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, pool_size=100, max_overflow=200)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

dev_engine = create_engine(Config.SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dev_engine)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

def get_db():
    """
    Get a database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

