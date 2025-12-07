"""
Pydantic схемы для диагностики.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

from app.models.diagnostic import DiagnosticMethod, MLLabel, QualityGrade


class DiagnosticBase(BaseModel):
    """Базовая схема диагностики согласно ТЗ."""
    object_id: int
    method: DiagnosticMethod
    date: date
    temperature: Optional[float] = None  # Температура воздуха
    humidity: Optional[float] = None  # Влажность
    illumination: Optional[float] = None  # Освещенность
    defect_found: bool = False
    defect_description: Optional[str] = None
    quality_grade: Optional[QualityGrade] = None  # Оценка качества
    param1: Optional[float] = None  # Параметр 1
    param2: Optional[float] = None  # Параметр 2
    param3: Optional[float] = None  # Параметр 3
    ml_label: Optional[MLLabel] = None


class DiagnosticCreate(DiagnosticBase):
    """Схема для создания диагностики."""
    pass


class DiagnosticUpdate(BaseModel):
    """Схема для обновления диагностики."""
    method: Optional[DiagnosticMethod] = None
    date: Optional[date] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    illumination: Optional[float] = None
    defect_found: Optional[bool] = None
    defect_description: Optional[str] = None
    quality_grade: Optional[QualityGrade] = None
    param1: Optional[float] = None
    param2: Optional[float] = None
    param3: Optional[float] = None
    ml_label: Optional[MLLabel] = None


class DiagnosticResponse(DiagnosticBase):
    """Схема ответа с диагностикой."""
    diag_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MLProbabilities(BaseModel):
    """Вероятности ML предсказаний."""
    normal: float
    medium: float
    high: float


class DiagnosticListItem(BaseModel):
    """Схема для списка диагностик (используется в /api/diagnostics/{object_id})."""
    diag_id: int
    object_id: int  # ID объекта из CSV (видимый пользователю)
    method: str
    date: str  # ISO format date
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    illumination: Optional[float] = None
    defect_found: bool
    defect_description: Optional[str] = None
    quality_grade: Optional[str] = None
    param1: Optional[float] = None
    param2: Optional[float] = None
    param3: Optional[float] = None
    ml_label: Optional[str] = None
    source_file: Optional[str] = None
    ml_probabilities: Optional[MLProbabilities] = None
    
    class Config:
        from_attributes = False  # Ручное создание из словаря

