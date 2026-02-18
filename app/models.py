from app.database import Base
from sqlalchemy import TIMESTAMP, Column, String, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy_utils import UUIDType
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False, index=True)
    last_name = Column(String(255), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    activated = Column(Boolean, nullable=False, default=True)
    createdAt = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updatedAt = Column(TIMESTAMP(timezone=True), default=None, onupdate=func.now())


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUIDType(binary=False), ForeignKey("users.id"), nullable=False, index=True
    )
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    createdAt = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
