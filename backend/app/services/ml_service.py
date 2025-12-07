"""
Сервис для работы с ML моделью с кэшированием и логированием.
"""
import pandas as pd
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.ml_model import ml_model
from app.core.redis_cache import get_cached_prediction, cache_prediction
from app.models.diagnostic import Diagnostic, MLLabel
from app.models.object import Object
from app.core.logging_config import logger


async def predict_diagnostics(
    session: AsyncSession,
    diagnostics: List[Dict],
    use_cache: bool = True,
    log_predictions: bool = True,
) -> List[str]:
    """
    Предсказание ml_label для диагностик без меток с кэшированием и логированием.
    
    Args:
        session: DB сессия
        diagnostics: Список словарей с данными диагностики
        use_cache: Использовать кэш Redis
        log_predictions: Логировать предсказания в БД
        
    Returns:
        Список предсказанных меток
    """
    if not diagnostics:
        return []
    
    # Создаем DataFrame
    df = pd.DataFrame(diagnostics)
    
    # Получаем годы объектов для контекста
    object_ids = df["object_id"].unique().tolist()
    if object_ids:
        stmt = select(Object.object_id, Object.year).where(
            Object.object_id.in_(object_ids)
        )
        result = await session.execute(stmt)
        object_years = {row[0]: row[1] for row in result}
        df["object_year"] = df["object_id"].map(object_years)
    
    # Добавляем дату если есть
    if "date" not in df.columns and "diagnostic_date" in df.columns:
        df["date"] = pd.to_datetime(df["diagnostic_date"], errors='coerce')
    
    predictions = []
    prediction_logs = []
    
    # Обрабатываем каждую диагностику (для кэширования и логирования)
    for idx, row in df.iterrows():
        # Формируем ключ для кэша
        features_dict = {
            "param1": float(row.get("param1", 0)),
            "param2": float(row.get("param2", 0)),
            "param3": float(row.get("param3", 0)),
            "method": str(row.get("method", "")),
            "defect_found": bool(row.get("defect_found", False)),
            "object_year": int(row.get("object_year", 2000)),
        }
        
        # Пытаемся получить из кэша
        cached_pred = None
        if use_cache:
            cached_pred = get_cached_prediction(features_dict)
        
        if cached_pred:
            pred = cached_pred["prediction"]
            logger.debug(f"Предсказание из кэша для диагностики {idx}")
        else:
            # Делаем предсказание
            row_df = pd.DataFrame([row])
            pred_list = ml_model.predict(row_df)
            pred = pred_list[0] if pred_list else "normal"
            
            # Сохраняем в кэш
            if use_cache:
                cache_prediction(features_dict, {"prediction": pred})
        
        predictions.append(pred)
        
        # Логируем предсказание
        if log_predictions and "diag_id" in row:
            prediction_logs.append({
                "diag_id": row["diag_id"],
                "prediction": pred,
                "features": features_dict,
                "timestamp": datetime.now(),
            })
    
    # Сохраняем логи в БД (если нужно)
    if log_predictions and prediction_logs:
        try:
            from app.models.ml_prediction_log import MLPredictionLog
            
            # Получаем вероятности для всех предсказаний одним батчем
            probabilities = ml_model.predict_proba(df)
            
            # Сохраняем логи
            for i, log_data in enumerate(prediction_logs):
                if i < len(predictions) and i < len(probabilities):
                    proba = probabilities[i]
                    # Предполагаем порядок классов: normal, medium, high (нужно проверить порядок в модели)
                    # Для безопасности используем индексы
                    log_entry = MLPredictionLog(
                        diag_id=log_data.get("diag_id"),
                        prediction=predictions[i],
                        probability_normal=float(proba[0]) if len(proba) > 0 else 0.33,
                        probability_medium=float(proba[1]) if len(proba) > 1 else 0.33,
                        probability_high=float(proba[2]) if len(proba) > 2 else 0.34,
                        features=log_data.get("features", {}),
                        model_version=ml_model.mlflow_run_id,
                    )
                    session.add(log_entry)
            
            await session.commit()
            logger.info(f"✅ Сохранено {len(prediction_logs)} логов предсказаний в БД")
        except Exception as e:
            logger.warning(f"Не удалось сохранить логи предсказаний: {e}")
            try:
                await session.rollback()
            except:
                pass
    
    return predictions


async def train_model_from_db(
    session: AsyncSession,
    use_mlflow: bool = True,
    test_size: float = None,
) -> Dict:
    """
    Обучение модели на размеченных данных из БД с метриками.
    
    Args:
        session: DB сессия
        use_mlflow: Использовать MLflow для логирования
        test_size: Размер тестовой выборки
        
    Returns:
        Статистика обучения с метриками
    """
    # Получаем размеченные данные
    stmt = (
        select(Diagnostic, Object.year)
        .join(Object, Diagnostic.object_id == Object.object_id)
        .where(Diagnostic.ml_label.isnot(None))
    )
    result = await session.execute(stmt)
    rows = result.all()
    
    # Минимум 100 записей для обучения
    min_samples = 100
    if len(rows) < min_samples:
        return {
            "trained": False,
            "message": f"Недостаточно данных для обучения. Нужно минимум {min_samples}, получено {len(rows)}",
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
    
    # Подготавливаем признаки и метки
    X = df.drop(columns=["ml_label"])
    y = df["ml_label"].values
    
    # Обучаем модель с метриками
    result = ml_model.train(X, y, use_mlflow=use_mlflow, test_size=test_size)
    
    return {
        "trained": True,
        "samples": len(rows),
        "metrics": result.get("metrics", {}),
        "train_size": result.get("train_size"),
        "test_size": result.get("test_size"),
        "mlflow_run_id": result.get("mlflow_run_id"),
    }
