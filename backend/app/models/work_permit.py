"""
Модель для наряда-допуска.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class WorkPermitStatus(str, enum.Enum):
    """Статус наряда-допуска."""
    ISSUED = "issued"  # Выдан
    ACTIVE = "active"  # Активен
    CLOSED = "closed"  # Закрыт
    CANCELLED = "cancelled"  # Отменен


class WorkPermit(Base):
    """Модель наряда-допуска."""
    __tablename__ = "work_permits"
    
    permit_id = Column(Integer, primary_key=True, index=True)
    permit_number = Column(String(50), unique=True, nullable=False, index=True)  # ND-2025-0001
    object_id = Column(Integer, ForeignKey("objects.id"), nullable=False, index=True)
    diagnostic_id = Column(Integer, ForeignKey("diagnostics.diag_id"), nullable=True, index=True)  # Последняя диагностика на момент выдачи
    status = Column(String(20), default=WorkPermitStatus.ISSUED.value, nullable=False, index=True)  # issued/active/closed/cancelled
    issued_date = Column(Date, nullable=False, index=True)
    issued_by = Column(String(255), nullable=True)  # Кто выдал наряд-допуск
    closed_date = Column(Date, nullable=True)  # Дата закрытия
    closed_by = Column(String(255), nullable=True)  # Кто закрыл
    notes = Column(String(1000), nullable=True)  # Дополнительные примечания
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    object = relationship("Object", back_populates="work_permits")
    diagnostic = relationship("Diagnostic", backref="work_permits")

