"""
Асинхронные задачи для обучения ML модели с использованием Celery или BackgroundTasks.
"""
from typing import Dict, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

try:
    from celery import Celery
    from app.core.config import settings
    
    celery_app = Celery(
        "integrityos_ml",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )
    CELERY_AVAILABLE = True
except Exception as e:
    CELERY_AVAILABLE = False
    celery_app = None

from fastapi import BackgroundTasks
from app.core.ml_model import ml_model
from app.models.diagnostic import Diagnostic
from app.models.object import Object
from app.core.logging_config import logger


def train_model_background_task(
    session: Session,
    use_mlflow: bool = True,
    optimize_hyperparams: bool = False,
) -> Dict:
    """
    Фоновая задача для обучения модели (для использования с BackgroundTasks).
    
    Args:
        session: DB сессия
        use_mlflow: Использовать MLflow
        optimize_hyperparams: Оптимизировать гиперпараметры
        
    Returns:
        Результат обучения
    """
    try:
        logger.info("Начало фонового обучения ML модели...")
        
        # Получаем размеченные данные
        stmt = (
            select(Diagnostic, Object.year)
            .join(Object, Diagnostic.object_id == Object.id)
            .where(Diagnostic.ml_label.isnot(None))
        )
        result = session.execute(stmt)
        rows = result.all()
        
        min_samples = 100
        if len(rows) < min_samples:
            return {
                "trained": False,
                "message": f"Недостаточно данных. Нужно минимум {min_samples}, получено {len(rows)}",
                "samples": len(rows),
            }
        
        # Подготавливаем данные
        data = []
        for diagnostic, year in rows:
            data.append({
                "param1": diagnostic.param1 or 0,
                "param2": diagnostic.param2 or 0,
                "param3": diagnostic.param3 or 0,
                "method": diagnostic.method.value,
                "defect_found": diagnostic.defect_found,
                "object_year": year or 2000,
                "date": diagnostic.date,
                "ml_label": diagnostic.ml_label.value,
            })
        
        df = pd.DataFrame(data)
        X = df.drop(columns=["ml_label"])
        y = df["ml_label"].values
        
        # Оптимизация гиперпараметров (если нужно)
        optimized_params = None
        if optimize_hyperparams:
            from app.services.ml_optimization import optimize_hyperparameters
            opt_result = optimize_hyperparameters(X, y, n_trials=30)
            if opt_result.get("optimized"):
                optimized_params = opt_result.get("best_params")
                logger.info(f"Используются оптимизированные параметры: {optimized_params}")
        
        # Обновляем параметры модели если есть оптимизированные
        if optimized_params:
            classifier = ml_model._pipeline.named_steps['classifier']
            for param, value in optimized_params.items():
                if hasattr(classifier, param):
                    setattr(classifier, param, value)
        
        # Обучаем модель
        result = ml_model.train(X, y, use_mlflow=use_mlflow)
        
        logger.info("✅ Фоновое обучение ML модели завершено")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при фоновом обучении модели: {e}", exc_info=True)
        return {
            "trained": False,
            "error": str(e),
        }


if CELERY_AVAILABLE:
    @celery_app.task(name="train_ml_model")
    def train_ml_model_task(
        use_mlflow: bool = True,
        optimize_hyperparams: bool = False,
    ) -> Dict:
        """
        Celery задача для обучения модели.
        
        Args:
            use_mlflow: Использовать MLflow
            optimize_hyperparams: Оптимизировать гиперпараметры
            
        Returns:
            Результат обучения
        """
        # Создаем новую сессию для задачи
        from app.core.database import SessionLocal
        session = SessionLocal()
        
        try:
            return train_model_background_task(
                session,
                use_mlflow=use_mlflow,
                optimize_hyperparams=optimize_hyperparams,
            )
        finally:
            session.close()


def schedule_training(
    background_tasks: BackgroundTasks,
    session: Session,
    use_mlflow: bool = True,
    optimize_hyperparams: bool = False,
    use_celery: bool = False,
) -> Dict:
    """
    Планирует обучение модели (через BackgroundTasks или Celery).
    
    Args:
        background_tasks: FastAPI BackgroundTasks
        session: DB сессия
        use_mlflow: Использовать MLflow
        optimize_hyperparams: Оптимизировать гиперпараметры
        use_celery: Использовать Celery вместо BackgroundTasks
        
    Returns:
        Информация о запланированной задаче
    """
    if use_celery and CELERY_AVAILABLE:
        # Используем Celery
        task = train_ml_model_task.delay(
            use_mlflow=use_mlflow,
            optimize_hyperparams=optimize_hyperparams,
        )
        return {
            "scheduled": True,
            "task_id": task.id,
            "method": "celery",
            "status": "pending",
        }
    else:
        # Используем BackgroundTasks
        background_tasks.add_task(
            train_model_background_task,
            session=session,
            use_mlflow=use_mlflow,
            optimize_hyperparams=optimize_hyperparams,
        )
        return {
            "scheduled": True,
            "method": "background_tasks",
            "status": "pending",
        }

