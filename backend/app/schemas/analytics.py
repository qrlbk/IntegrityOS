"""
Pydantic схемы для аналитики.
"""
from pydantic import BaseModel, Field
from typing import List


class DefectsTimelineItem(BaseModel):
    """Элемент временной линии дефектов."""
    year: int = Field(..., ge=1900, le=2100)
    total: int = Field(..., ge=0)
    defects: int = Field(..., ge=0)
    percentage: float = Field(..., ge=0.0, le=100.0)
    
    class Config:
        from_attributes = False


