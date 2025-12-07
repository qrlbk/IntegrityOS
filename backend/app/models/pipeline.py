"""
Модель для трубопровода.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Pipeline(Base):
    """Модель трубопровода."""
    __tablename__ = "pipelines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)  # Например, "MT-01"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    objects = relationship("Object", back_populates="pipeline", cascade="all, delete-orphan")

