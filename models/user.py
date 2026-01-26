from sqlalchemy import Column, Integer, String
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tg_user_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, index=True)
