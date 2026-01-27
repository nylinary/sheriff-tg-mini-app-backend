from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine

from settings import settings


POSTGRES_DSN = settings.postgres_dsn
POSTGRES_DSN_SYNC = POSTGRES_DSN.replace("+asyncpg", "") if POSTGRES_DSN else ""

Base = declarative_base()

_engine = None
_SessionLocal = None
_alembic_engine = None


def get_engine():
    global _engine
    if _engine is None:
        if not POSTGRES_DSN or "://" not in POSTGRES_DSN:
            raise RuntimeError("POSTGRES_DSN is not configured")
        _engine = create_async_engine(POSTGRES_DSN, echo=True, future=True)
    return _engine


def get_sessionmaker():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _SessionLocal


def get_alembic_engine():
    global _alembic_engine
    if _alembic_engine is None:
        if not POSTGRES_DSN_SYNC or "://" not in POSTGRES_DSN_SYNC:
            raise RuntimeError("POSTGRES_DSN is not configured")
        _alembic_engine = create_engine(POSTGRES_DSN_SYNC, echo=True, future=True)
    return _alembic_engine


# Backwards-compatible names (created lazily)
class _LazySessionLocal:
    def __call__(self, *args, **kwargs):
        return get_sessionmaker()(*args, **kwargs)


SessionLocal = _LazySessionLocal()


@property
def engine():  # type: ignore
    return get_engine()


@property
def alembic_engine():  # type: ignore
    return get_alembic_engine()
