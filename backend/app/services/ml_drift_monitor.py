"""
Мониторинг дрифта данных и модели с использованием Evidently AI.
"""
from typing import Dict, Optional, List
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, func

try:
    from evidently import ColumnMapping
    from evidently.report import Report
    from evidently.metric_preset import (
        DataDriftPreset,
        DataQualityPreset,
        TargetDriftPreset,
    )
    from evidently.metrics import (
        DatasetDriftMetric,
        ColumnDriftMetric,
    )
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False

from app.models.diagnostic import Diagnostic
from app.models.object import Object
from app.core.logging_config import logger


def collect_reference_data(session: Session, days_back: int = 30) -> pd.DataFrame:
    """
    Собирает референсные данные для сравнения.
    
    Args:
        session: DB сессия
        days_back: Сколько дней назад брать данные
        
    Returns:
        DataFrame с референсными данными
    """
    cutoff_date = datetime.now().date() - timedelta(days=days_back)
    
    stmt = (
        select(
            Diagnostic.param1,
            Diagnostic.param2,
            Diagnostic.param3,
            Diagnostic.method,
            Diagnostic.defect_found,
            Diagnostic.ml_label,
            Object.year.label("object_year"),
        )
        .join(Object, Diagnostic.object_id == Object.id)
        .where(Diagnostic.date >= cutoff_date)
        .where(Diagnostic.ml_label.isnot(None))
    )
    
    result = session.execute(stmt)
    rows = result.all()
    
    if not rows:
        return pd.DataFrame()
    
    data = []
    for row in rows:
        data.append({
            "param1": row.param1 or 0,
            "param2": row.param2 or 0,
            "param3": row.param3 or 0,
            "method": row.method.value if hasattr(row.method, 'value') else str(row.method),
            "defect_found": row.defect_found,
            "ml_label": row.ml_label.value if hasattr(row.ml_label, 'value') else str(row.ml_label),
            "object_year": row.object_year or 2000,
        })
    
    return pd.DataFrame(data)


def collect_current_data(session: Session, days_back: int = 7) -> pd.DataFrame:
    """
    Собирает текущие данные для сравнения с референсом.
    
    Args:
        session: DB сессия
        days_back: Сколько дней назад брать данные
        
    Returns:
        DataFrame с текущими данными
    """
    cutoff_date = datetime.now().date() - timedelta(days=days_back)
    
    stmt = (
        select(
            Diagnostic.param1,
            Diagnostic.param2,
            Diagnostic.param3,
            Diagnostic.method,
            Diagnostic.defect_found,
            Diagnostic.ml_label,
            Object.year.label("object_year"),
        )
        .join(Object, Diagnostic.object_id == Object.id)
        .where(Diagnostic.date >= cutoff_date)
    )
    
    result = session.execute(stmt)
    rows = result.all()
    
    if not rows:
        return pd.DataFrame()
    
    data = []
    for row in rows:
        data.append({
            "param1": row.param1 or 0,
            "param2": row.param2 or 0,
            "param3": row.param3 or 0,
            "method": row.method.value if hasattr(row.method, 'value') else str(row.method),
            "defect_found": row.defect_found,
            "ml_label": row.ml_label.value if row.ml_label and hasattr(row.ml_label, 'value') else (str(row.ml_label) if row.ml_label else None),
            "object_year": row.object_year or 2000,
        })
    
    return pd.DataFrame(data)


def check_data_drift(session: Session) -> Optional[Dict]:
    """
    Проверяет дрифт данных с помощью Evidently AI.
    
    Args:
        session: DB сессия
        
    Returns:
        Словарь с результатами проверки дрифта или None если Evidently недоступен
    """
    if not EVIDENTLY_AVAILABLE:
        logger.warning("Evidently AI не установлен. Установите: pip install evidently")
        return None
    
    try:
        # Собираем данные
        reference_data = collect_reference_data(session, days_back=30)
        current_data = collect_current_data(session, days_back=7)
        
        if reference_data.empty or current_data.empty:
            return {
                "drift_detected": False,
                "message": "Недостаточно данных для проверки дрифта",
                "reference_samples": len(reference_data),
                "current_samples": len(current_data),
            }
        
        # Настраиваем ColumnMapping
        column_mapping = ColumnMapping()
        column_mapping.numerical_features = ["param1", "param2", "param3", "object_year"]
        column_mapping.categorical_features = ["method"]
        column_mapping.target = "ml_label"
        column_mapping.prediction = None
        
        # Создаем отчет о дрифте данных
        data_drift_report = Report(metrics=[DataDriftPreset()])
        data_drift_report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping
        )
        
        # Получаем метрики
        metrics = data_drift_report.as_dict()
        
        # Проверяем наличие дрифта
        drift_detected = False
        drift_score = 0.0
        
        if "metrics" in metrics:
            for metric in metrics["metrics"]:
                if metric.get("metric") == "DatasetDriftMetric":
                    drift_detected = metric.get("result", {}).get("dataset_drift", False)
                    drift_score = metric.get("result", {}).get("drift_score", 0.0)
                    break
        
        result = {
            "drift_detected": drift_detected,
            "drift_score": drift_score,
            "reference_samples": len(reference_data),
            "current_samples": len(current_data),
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
        }
        
        if drift_detected:
            logger.warning(f"⚠️  Обнаружен дрифт данных! Score: {drift_score:.4f}")
        else:
            logger.info(f"✅ Дрифт данных не обнаружен. Score: {drift_score:.4f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при проверке дрифта данных: {e}", exc_info=True)
        return {
            "drift_detected": None,
            "error": str(e),
        }


def check_target_drift(session: Session) -> Optional[Dict]:
    """
    Проверяет дрифт целевой переменной (ml_label).
    
    Args:
        session: DB сессия
        
    Returns:
        Словарь с результатами проверки дрифта целевой переменной
    """
    if not EVIDENTLY_AVAILABLE:
        return None
    
    try:
        reference_data = collect_reference_data(session, days_back=30)
        current_data = collect_current_data(session, days_back=7)
        
        if reference_data.empty or current_data.empty or "ml_label" not in reference_data.columns:
            return {
                "drift_detected": False,
                "message": "Недостаточно данных для проверки дрифта целевой переменной",
            }
        
        # Фильтруем только данные с метками
        reference_data = reference_data[reference_data["ml_label"].notna()]
        current_data = current_data[current_data["ml_label"].notna()]
        
        if len(reference_data) < 10 or len(current_data) < 10:
            return {
                "drift_detected": False,
                "message": "Недостаточно размеченных данных",
            }
        
        column_mapping = ColumnMapping()
        column_mapping.target = "ml_label"
        
        target_drift_report = Report(metrics=[TargetDriftPreset()])
        target_drift_report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping
        )
        
        metrics = target_drift_report.as_dict()
        
        drift_detected = False
        for metric in metrics.get("metrics", []):
            if "drift" in metric.get("metric", "").lower():
                drift_detected = metric.get("result", {}).get("drift_detected", False)
                break
        
        return {
            "drift_detected": drift_detected,
            "reference_samples": len(reference_data),
            "current_samples": len(current_data),
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Ошибка при проверке дрифта целевой переменной: {e}", exc_info=True)
        return None

