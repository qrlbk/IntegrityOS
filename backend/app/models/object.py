"""
Модель для объектов (оборудование).
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class ObjectType(str, enum.Enum):
    """Типы объектов."""
    CRANE = "crane"
    COMPRESSOR = "compressor"
    PIPELINE_SECTION = "pipeline_section"


class LocationStatus(str, enum.Enum):
    """Статус местоположения объекта."""
    PENDING = "pending"  # Координаты не установлены (автocозданный объект)
    VERIFIED = "verified"  # Координаты установлены и проверены
    NEEDS_UPDATE = "needs_update"  # Координаты требуют обновления


class Object(Base):
    """Модель объекта (оборудование)."""
    __tablename__ = "objects"
    
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, unique=True, nullable=False, index=True)  # ID из CSV
    object_name = Column(String(255), nullable=False)
    object_type = Column(Enum(ObjectType), nullable=False)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False, index=True)
    lat = Column(Float, nullable=True)  # Может быть None для автocозданных объектов
    lon = Column(Float, nullable=True)  # Может быть None для автocозданных объектов
    # Используем String вместо Enum для совместимости с SQLite (enum хранится как строка)
    location_status = Column(String(20), default=LocationStatus.PENDING.value, nullable=False, index=True)
    year = Column(Integer)
    material = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="objects")
    diagnostics = relationship("Diagnostic", back_populates="object", cascade="all, delete-orphan")
    work_permits = relationship("WorkPermit", back_populates="object", cascade="all, delete-orphan")

