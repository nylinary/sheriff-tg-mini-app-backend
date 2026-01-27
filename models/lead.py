from sqlalchemy import Column, Integer, String, BigInteger, DateTime, JSON, func
from db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    tg_user_id = Column(BigInteger, index=True, nullable=False)
    username = Column(String, index=True, nullable=True)

    city = Column(String, nullable=False)
    exchange_type = Column(String, nullable=False)
    receive_type = Column(String, nullable=False)
    sum = Column(String, nullable=False)
    wallet_address = Column(String, nullable=False)

    meta = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
