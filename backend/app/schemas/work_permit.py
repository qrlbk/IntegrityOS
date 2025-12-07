"""
Pydantic схемы для наряда-допуска.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

from app.models.work_permit import WorkPermitStatus


class WorkPermitBase(BaseModel):
    """Базовая схема наряда-допуска."""
    object_id: int
    diagnostic_id: Optional[int] = None
    status: str = WorkPermitStatus.ISSUED.value
    issued_date: date
    issued_by: Optional[str] = None
    notes: Optional[str] = None


class WorkPermitCreate(WorkPermitBase):
    """Схема для создания наряда-допуска."""
    pass


class WorkPermitUpdate(BaseModel):
    """Схема для обновления наряда-допуска."""
    status: Optional[str] = None
    closed_date: Optional[date] = None
    closed_by: Optional[str] = None
    notes: Optional[str] = None


class WorkPermitResponse(WorkPermitBase):
    """Схема ответа с нарядом-допуском."""
    permit_id: int
    permit_number: str
    closed_date: Optional[date] = None
    closed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkPermitListItem(BaseModel):
    """Схема для списка нарядов-допусков."""
    permit_id: int
    permit_number: str
    object_id: int
    object_name: Optional[str] = None
    status: str
    issued_date: str  # ISO format
    issued_by: Optional[str] = None
    closed_date: Optional[str] = None
    
    class Config:
        from_attributes = False

