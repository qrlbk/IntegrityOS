"""
API endpoints для мониторинга ML модели с OpenAI и новыми возможностями.
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ml_monitor import (
    collect_ml_metrics,
    analyze_ml_with_ai,
    suggest_model_improvements,
    monitor_and_improve,
)
from app.services.import_service import _train_model_sync
from app.services.ml_drift_monitor import check_data_drift, check_target_drift
from app.services.ml_optimization import optimize_hyperparameters
from app.services.ml_training_tasks import schedule_training
from app.core.ml_model import ml_model

router = APIRouter()


@router.get("/ml/monitor/metrics")
def get_ml_metrics(
    session: Session = Depends(get_db),
):
    """
    Получить метрики работы ML модели.
    """
    metrics = collect_ml_metrics(session)
    return metrics


@router.get("/ml/monitor/analysis")
def get_ml_analysis(
    session: Session = Depends(get_db),
):
    """
    Получить анализ ML модели от OpenAI.
    Требует настройки OPENAI_API_KEY.
    """
    metrics = collect_ml_metrics(session)
    analysis = analyze_ml_with_ai(session, metrics)
    
    if analysis is None:
        return {
            "error": "OpenAI API не настроен. Добавьте OPENAI_API_KEY в .env файл.",
            "metrics": metrics
        }
    
    return {
        "metrics": metrics,
        "analysis": analysis
    }


@router.get("/ml/monitor/suggestions")
def get_ml_suggestions(
    session: Session = Depends(get_db),
):
    """
    Получить рекомендации по улучшению ML модели.
    """
    suggestions = suggest_model_improvements(session)
    return suggestions


@router.post("/ml/monitor/full")
def full_ml_monitor(
    session: Session = Depends(get_db),
    auto_improve: bool = Query(False, description="Автоматически применять безопасные улучшения"),
):
    """
    Полный мониторинг ML модели с анализом от OpenAI и рекомендациями.
    """
    result = monitor_and_improve(session, auto_improve=auto_improve)
    return result


@router.post("/ml/train")
def train_ml_model(
    session: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    async_mode: bool = Query(False, description="Обучать асинхронно в фоне"),
    optimize_hyperparams: bool = Query(False, description="Оптимизировать гиперпараметры перед обучением"),
):
    """
    Обучение ML модели на размеченных данных из БД.
    
    Требуется минимум 100 размеченных записей (с ml_label).
    
    Args:
        async_mode: Если True, обучение выполняется в фоне
        optimize_hyperparams: Если True, оптимизирует гиперпараметры перед обучением
    """
    if async_mode and background_tasks:
        # Асинхронное обучение
        task_info = schedule_training(
            background_tasks,
            session,
            use_mlflow=True,
            optimize_hyperparams=optimize_hyperparams,
            use_celery=False,  # Можно включить Celery если настроен
        )
        return {
            "message": "Обучение модели запущено в фоне",
            "task_info": task_info,
        }
    else:
        # Синхронное обучение
        result = _train_model_sync(session)
        return result


@router.post("/ml/optimize")
def optimize_ml_model(
    session: Session = Depends(get_db),
    n_trials: int = Query(30, description="Количество попыток оптимизации"),
):
    """
    Оптимизация гиперпараметров ML модели с помощью Optuna.
    """
    # Получаем данные для оптимизации
    from sqlalchemy import select
    from app.models.diagnostic import Diagnostic
    from app.models.object import Object
    import pandas as pd
    
    stmt = (
        select(Diagnostic, Object.year)
        .join(Object, Diagnostic.object_id == Object.id)
        .where(Diagnostic.ml_label.isnot(None))
    )
    result = session.execute(stmt)
    rows = result.all()
    
    if len(rows) < 100:
        return {
            "optimized": False,
            "message": f"Недостаточно данных. Нужно минимум 100, получено {len(rows)}",
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
    
    # Оптимизируем
    result = optimize_hyperparameters(X, y, n_trials=n_trials)
    return result


@router.get("/ml/drift")
def check_ml_drift(session: Session = Depends(get_db)):
    """
    Проверка дрифта данных с помощью Evidently AI.
    """
    data_drift = check_data_drift(session)
    target_drift = check_target_drift(session)
    
    return {
        "data_drift": data_drift,
        "target_drift": target_drift,
    }


@router.get("/ml/status")
def get_ml_status(session: Session = Depends(get_db)):
    """Получить статус ML модели."""
    metrics = collect_ml_metrics(session)
    model_metrics = ml_model.metrics
    
    return {
        "is_trained": ml_model.is_trained,
        "model_type": "RandomForestClassifier with Pipeline",
        "labeled_samples": metrics.get("with_ml_label", 0),
        "total_samples": metrics.get("total_diagnostics", 0),
        "mlflow_run_id": ml_model.mlflow_run_id,
        "training_metrics": model_metrics,
    }


