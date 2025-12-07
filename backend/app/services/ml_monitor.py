"""
Сервис мониторинга ML модели с использованием OpenAI API.
Анализирует работу модели и предоставляет рекомендации по улучшению.
"""
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import pandas as pd

from app.models.diagnostic import Diagnostic, MLLabel
from app.models.object import Object
from app.core.ml_model import ml_model
from app.core.config import settings
from app.core.logging_config import logger

try:
    from openai import OpenAI
    
    # Инициализируем клиент OpenAI
    openai_key = getattr(settings, 'OPENAI_API_KEY', None) or ""
    openai_key = openai_key.strip() if openai_key else ""
    
    if openai_key and openai_key.startswith('sk-') and len(openai_key) > 20:
        openai_client = OpenAI(api_key=openai_key)
    else:
        openai_client = None
except ImportError:
    openai_client = None
except Exception as e:
    openai_client = None
    logger.warning(f"OpenAI клиент не инициализирован: {e}")


def collect_ml_metrics(session: Session) -> Dict:
    """
    Собирает метрики работы ML модели.
    
    Returns:
        Словарь с метриками
    """
    metrics = {
        "model_trained": ml_model.is_trained,
        "total_diagnostics": 0,
        "with_ml_label": 0,
        "without_ml_label": 0,
        "predictions_distribution": {},
        "accuracy_estimate": None,
        "recent_predictions": 0,
        "method_distribution": {},
        "defect_rate": 0.0,
    }
    
    # Общая статистика
    total = session.query(func.count(Diagnostic.diag_id)).scalar() or 0
    metrics["total_diagnostics"] = total
    
    # С метками
    with_labels = (
        session.query(func.count(Diagnostic.diag_id))
        .filter(Diagnostic.ml_label.isnot(None))
        .scalar() or 0
    )
    metrics["with_ml_label"] = with_labels
    metrics["without_ml_label"] = total - with_labels
    
    # Распределение по меткам
    label_dist = (
        session.query(Diagnostic.ml_label, func.count(Diagnostic.diag_id))
        .filter(Diagnostic.ml_label.isnot(None))
        .group_by(Diagnostic.ml_label)
        .all()
    )
    
    for label, count in label_dist:
        metrics["predictions_distribution"][label.value if hasattr(label, 'value') else str(label)] = count
    
    # Распределение по методам
    method_dist = (
        session.query(Diagnostic.method, func.count(Diagnostic.diag_id))
        .group_by(Diagnostic.method)
        .all()
    )
    
    for method, count in method_dist:
        method_name = method.value if hasattr(method, 'value') else str(method)
        metrics["method_distribution"][method_name] = count
    
    # Процент дефектов
    defects = (
        session.query(func.count(Diagnostic.diag_id))
        .filter(Diagnostic.defect_found == True)
        .scalar() or 0
    )
    metrics["defect_rate"] = (defects / total * 100) if total > 0 else 0.0
    
    # Недавние предсказания (за последние 7 дней)
    week_ago = datetime.now().date() - timedelta(days=7)
    recent = (
        session.query(func.count(Diagnostic.diag_id))
        .filter(
            and_(
                Diagnostic.date >= week_ago,
                Diagnostic.ml_label.isnot(None)
            )
        )
        .scalar() or 0
    )
    metrics["recent_predictions"] = recent
    
    # Оценка точности (на основе распределения - если слишком много high, возможно переобучение)
    if metrics["predictions_distribution"]:
        high_count = metrics["predictions_distribution"].get("high", 0)
        medium_count = metrics["predictions_distribution"].get("medium", 0)
        normal_count = metrics["predictions_distribution"].get("normal", 0)
        total_labeled = high_count + medium_count + normal_count
        
        if total_labeled > 0:
            # Если >50% high - возможно переобучение или реальная проблема
            high_percentage = (high_count / total_labeled) * 100
            if high_percentage > 50:
                metrics["accuracy_estimate"] = "low"  # Возможно переобучение
            elif high_percentage < 5:
                metrics["accuracy_estimate"] = "medium"  # Возможно недообучение
            else:
                metrics["accuracy_estimate"] = "good"  # Нормальное распределение
    
    return metrics


def analyze_ml_with_ai(session: Session, metrics: Dict) -> Optional[Dict]:
    """
    Анализирует метрики ML модели с помощью OpenAI API.
    
    Args:
        session: DB сессия
        metrics: Собранные метрики
        
    Returns:
        Словарь с анализом и рекомендациями или None если OpenAI недоступен
    """
    if openai_client is None:
        return None
    
    # Формируем промпт для анализа
    system_prompt = """Ты эксперт по машинному обучению, специализирующийся на анализе моделей классификации.
Твоя задача - проанализировать метрики ML модели для системы мониторинга трубопроводов и дать рекомендации по улучшению.

Отвечай структурированно:
1. Краткая оценка текущего состояния модели
2. Выявленные проблемы (если есть)
3. Конкретные рекомендации по улучшению
4. Предложения по донастройке параметров модели

Будь конкретным и практичным."""
    
    user_prompt = f"""Проанализируй метрики ML модели для классификации критичности дефектов трубопроводов:

МЕТРИКИ:
- Модель обучена: {metrics.get('model_trained', False)}
- Всего диагностик: {metrics.get('total_diagnostics', 0)}
- С метками ML: {metrics.get('with_ml_label', 0)}
- Без меток: {metrics.get('without_ml_label', 0)}
- Распределение предсказаний: {json.dumps(metrics.get('predictions_distribution', {}), ensure_ascii=False)}
- Распределение по методам: {json.dumps(metrics.get('method_distribution', {}), ensure_ascii=False)}
- Процент дефектов: {metrics.get('defect_rate', 0):.2f}%
- Оценка точности: {metrics.get('accuracy_estimate', 'unknown')}
- Недавние предсказания (7 дней): {metrics.get('recent_predictions', 0)}

КОНТЕКСТ:
- Модель: RandomForestClassifier (100 деревьев, max_depth=10)
- Признаки: param1, param2, method, defect_found, object_year
- Классы: normal, medium, high
- Минимум для обучения: 100 записей

Дай анализ и рекомендации."""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        analysis_text = response.choices[0].message.content
        
        # Парсим ответ для извлечения рекомендаций
        recommendations = []
        if "рекомендации" in analysis_text.lower() or "рекомендации" in analysis_text.lower():
            # Пытаемся извлечь список рекомендаций
            lines = analysis_text.split('\n')
            for line in lines:
                if any(marker in line.lower() for marker in ['-', '•', '1.', '2.', '3.', '4.']):
                    if len(line.strip()) > 10:  # Игнорируем очень короткие строки
                        recommendations.append(line.strip())
        
        return {
            "analysis": analysis_text,
            "recommendations": recommendations if recommendations else [analysis_text],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Ошибка при анализе ML модели через OpenAI: {e}")
        return None


def suggest_model_improvements(session: Session) -> Dict:
    """
    Предлагает улучшения модели на основе анализа.
    
    Returns:
        Словарь с рекомендациями
    """
    metrics = collect_ml_metrics(session)
    ai_analysis = analyze_ml_with_ai(session, metrics)
    
    result = {
        "metrics": metrics,
        "ai_analysis": ai_analysis,
        "suggestions": [],
    }
    
    # Автоматические предложения на основе метрик
    if not metrics["model_trained"]:
        result["suggestions"].append({
            "type": "training",
            "priority": "high",
            "message": "Модель не обучена. Импортируйте данные с метками ml_label (минимум 100 записей).",
            "action": "POST /api/ml/train"
        })
    elif metrics["with_ml_label"] < 100:
        result["suggestions"].append({
            "type": "data",
            "priority": "medium",
            "message": f"Мало размеченных данных ({metrics['with_ml_label']}). Рекомендуется минимум 100 для качественного обучения.",
            "action": "Импортируйте больше данных с метками ml_label"
        })
    
    # Проверка распределения
    if metrics["predictions_distribution"]:
        high_pct = (metrics["predictions_distribution"].get("high", 0) / 
                   max(sum(metrics["predictions_distribution"].values()), 1) * 100)
        
        if high_pct > 50:
            result["suggestions"].append({
                "type": "overfitting",
                "priority": "medium",
                "message": f"Высокий процент критических предсказаний ({high_pct:.1f}%). Возможно переобучение модели.",
                "action": "Рассмотрите увеличение max_depth или уменьшение n_estimators"
            })
        elif high_pct < 2:
            result["suggestions"].append({
                "type": "underfitting",
                "priority": "low",
                "message": f"Очень низкий процент критических предсказаний ({high_pct:.1f}%). Возможно модель слишком консервативна.",
                "action": "Проверьте баланс классов при обучении"
            })
    
    # Проверка разнообразия методов
    if len(metrics["method_distribution"]) < 3:
        result["suggestions"].append({
            "type": "diversity",
            "priority": "low",
            "message": "Мало разнообразия в методах диагностики. Модель может быть менее точной для редких методов.",
            "action": "Импортируйте данные с разными методами диагностики"
        })
    
    return result


def monitor_and_improve(session: Session, auto_improve: bool = False) -> Dict:
    """
    Мониторит модель и предлагает улучшения.
    Может автоматически применять некоторые улучшения.
    
    Args:
        session: DB сессия
        auto_improve: Если True, автоматически применяет безопасные улучшения
        
    Returns:
        Словарь с результатами мониторинга
    """
    logger.info("Начало мониторинга ML модели...")
    
    metrics = collect_ml_metrics(session)
    ai_analysis = analyze_ml_with_ai(session, metrics)
    suggestions = suggest_model_improvements(session)
    
    result = {
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "ai_analysis": ai_analysis,
        "suggestions": suggestions.get("suggestions", []),
        "auto_improvements_applied": [],
    }
    
    # Автоматические улучшения (только безопасные)
    if auto_improve and ai_analysis:
        # Здесь можно добавить логику автоматической донастройки
        # Например, переобучение с другими параметрами
        logger.info("Автоматические улучшения не реализованы (требуется ручное подтверждение)")
    
    logger.info("Мониторинг ML модели завершен")
    return result


