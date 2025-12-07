"""
Модель для логирования предсказаний ML модели.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MLPredictionLog(Base):
    """Модель для логирования предсказаний ML модели."""
    __tablename__ = "ml_prediction_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    diag_id = Column(Integer, ForeignKey("diagnostics.diag_id"), nullable=True, index=True)
    prediction = Column(String(50), nullable=False, index=True)  # normal, medium, high
    probability_normal = Column(Float)
    probability_medium = Column(Float)
    probability_high = Column(Float)
    features = Column(JSON)  # Сохраняем признаки для анализа
    model_version = Column(String(100))  # Версия модели (MLflow run_id)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    diagnostic = relationship("Diagnostic", backref="ml_prediction_logs")

