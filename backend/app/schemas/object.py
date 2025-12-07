"""
Pydantic схемы для объектов.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.object import ObjectType


class ObjectBase(BaseModel):
    """Базовая схема объекта."""
    object_name: str = Field(..., max_length=255)
    object_type: ObjectType
    pipeline_id: str = Field(..., max_length=10)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    material: Optional[str] = Field(None, max_length=100)


class ObjectCreate(ObjectBase):
    """Схема для создания объекта."""
    pass


class ObjectUpdate(BaseModel):
    """Схема для обновления объекта."""
    object_name: Optional[str] = None
    object_type: Optional[ObjectType] = None
    pipeline_id: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    year: Optional[int] = None
    material: Optional[str] = None


class ObjectResponse(ObjectBase):
    """Схема ответа с объектом."""
    object_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ObjectWithRisk(ObjectResponse):
    """Объект с информацией о риске."""
    risk_level: Optional[str] = None  # normal, medium, high
    last_diagnostic_date: Optional[datetime] = None


class ObjectListItem(BaseModel):
    """Схема для списка объектов (используется в /api/objects)."""
    id: int
    name: str
    type: str
    lat: Optional[float] = None  # Может быть None для объектов без координат
    lon: Optional[float] = None  # Может быть None для объектов без координат
    status: str  # "Critical" или "Normal"
    pipeline_id: Optional[str] = None
    location_status: Optional[str] = None  # "pending", "verified", "needs_update"
    risk_level: Optional[str] = None  # "normal", "medium", "high" - из ml_label последней диагностики
    
    class Config:
        from_attributes = False  # Ручное создание из словаря

