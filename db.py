from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine  # Add sync engine for Alembic
import os

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
POSTGRES_DSN_SYNC = POSTGRES_DSN.replace("+asyncpg", "")  # For Alembic

engine = create_async_engine(POSTGRES_DSN, echo=True, future=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Synchronous engine for Alembic
alembic_engine = create_engine(POSTGRES_DSN_SYNC, echo=True, future=True)
