from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine

from settings import settings


POSTGRES_DSN = settings.postgres_dsn
POSTGRES_DSN_SYNC = POSTGRES_DSN.replace("+asyncpg", "")

engine = create_async_engine(POSTGRES_DSN, echo=True, future=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

alembic_engine = create_engine(POSTGRES_DSN_SYNC, echo=True, future=True)
