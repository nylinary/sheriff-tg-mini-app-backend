from sqlalchemy import Column, Integer, String, DateTime, JSON, func
from db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    # Store as string to avoid integer overflow and keep exact value
    tg_user_id = Column(String, index=True, nullable=False)
    username = Column(String, index=True, nullable=True)

    city = Column(String, nullable=False)
    exchange_type = Column(String, nullable=False)
    receive_type = Column(String, nullable=False)
    sum = Column(String, nullable=False)
    wallet_address = Column(String, nullable=False)

    meta = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
