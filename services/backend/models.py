from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .db import Base


class Credential(Base):
    __tablename__ = "credentials"
    id = Column(Integer, primary_key=True, index=True)
    broker = Column(String(64), index=True)
    username_encrypted = Column(Text, nullable=False)
    password_encrypted = Column(Text, nullable=False)
    notes_encrypted = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
