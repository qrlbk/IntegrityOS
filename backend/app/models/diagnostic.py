"""
Модель для диагностики.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class DiagnosticMethod(str, enum.Enum):
    """Методы диагностики согласно ТЗ."""
    VIK = "VIK"
    PVK = "PVK"
    MPK = "MPK"
    UZK = "UZK"
    RGK = "RGK"
    TVK = "TVK"
    VIBRO = "VIBRO"
    MFL = "MFL"
    TFI = "TFI"
    GEO = "GEO"
    UTWM = "UTWM"
    UT = "UT"  # Ультразвуковая дефектоскопия
    EC = "EC"  # Электромагнитный контроль


class MLLabel(str, enum.Enum):
    """ML метки критичности."""
    NORMAL = "normal"
    MEDIUM = "medium"
    HIGH = "high"


class QualityGrade(str, enum.Enum):
    """Оценка качества согласно ТЗ."""
    УДОВЛЕТВОРИТЕЛЬНО = "удовлетворительно"
    ДОПУСТИМО = "допустимо"
    ТРЕБУЕТ_МЕР = "требует_мер"
    НЕДОПУСТИМО = "недопустимо"


class Diagnostic(Base):
    """Модель диагностики согласно ТЗ."""
    __tablename__ = "diagnostics"
    
    diag_id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id"), nullable=False, index=True)
    method = Column(Enum(DiagnosticMethod), nullable=False, index=True)
    date = Column(Date, nullable=False)
    temperature = Column(Float)  # Температура воздуха
    humidity = Column(Float)  # Влажность
    illumination = Column(Float)  # Освещенность
    defect_found = Column(Boolean, default=False)
    defect_description = Column(Text)
    quality_grade = Column(Enum(QualityGrade))  # Оценка качества
    param1 = Column(Float)  # Параметр 1 (глубина, виброскорость, толщина и т.п.)
    param2 = Column(Float)  # Параметр 2
    param3 = Column(Float)  # Параметр 3
    ml_label = Column(Enum(MLLabel), index=True)
    source_file = Column(String(255))  # Исходный файл импорта
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    object = relationship("Object", back_populates="diagnostics")

