from sqlalchemy import Column, Integer, String
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # Store as string to avoid any integer overflow and keep exact value
    tg_user_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True)
