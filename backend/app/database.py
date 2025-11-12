"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = settings.DATABASE_URL

# Create async engine (with SQLite optimizations)
if "sqlite" in DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL or other databases
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )

# Session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    """Get database session."""
    async with async_session() as session:
        yield session

# Dependency for FastAPI
def get_db():
    """Dependency to get DB session in sync endpoints."""
    return async_session
