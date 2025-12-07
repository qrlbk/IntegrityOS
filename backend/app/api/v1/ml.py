"""
API endpoints для ML модели.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.ml_model import ml_model
from app.services.ml_service import train_model_from_db

router = APIRouter()


@router.post("/ml/train")
async def train_model(
    session: AsyncSession = Depends(get_db),
):
    """
    Обучение ML модели на размеченных данных из БД.
    
    Требуется минимум 100 размеченных записей (с ml_label).
    """
    result = await train_model_from_db(session)
    return result


@router.get("/ml/status")
async def get_ml_status():
    """Получить статус ML модели."""
    return {
        "is_trained": ml_model.is_trained,
        "model_type": "RandomForestClassifier",
    }

