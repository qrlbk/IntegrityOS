"""
API endpoints для диагностики.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

from app.core.database import get_db
from app.models.object import Object
from app.models.diagnostic import Diagnostic, DiagnosticMethod, QualityGrade, MLLabel
from app.schemas.diagnostic import DiagnosticListItem, DiagnosticCreate
from datetime import date

# Импортируем ml_model только там, где он нужен
try:
    from app.core.ml_model import ml_model
except ImportError:
    ml_model = None

router = APIRouter()


@router.get("/diagnostics", response_model=List[DiagnosticListItem])
def get_diagnostics(
    limit: Optional[int] = 10,
    sort_by: Optional[str] = "date",
    sort_order: Optional[str] = "desc",
    session: Session = Depends(get_db),
):
    """
    Возвращает список диагностик с фильтрацией и сортировкой.
    
    Args:
        limit: Максимальное количество диагностик для возврата
        sort_by: Поле для сортировки (date, diag_id)
        sort_order: Порядок сортировки (asc, desc)
    """
    from sqlalchemy.orm import joinedload
    
    query = session.query(Diagnostic).options(joinedload(Diagnostic.object))
    
    # Применяем сортировку
    if sort_by == "date":
        if sort_order == "desc":
            query = query.order_by(desc(Diagnostic.date))
        else:
            query = query.order_by(Diagnostic.date)
    elif sort_by == "diag_id":
        if sort_order == "desc":
            query = query.order_by(desc(Diagnostic.diag_id))
        else:
            query = query.order_by(Diagnostic.diag_id)
    else:
        # По умолчанию сортируем по дате в убывающем порядке
        query = query.order_by(desc(Diagnostic.date))
    
    # Применяем лимит
    if limit:
        query = query.limit(limit)
    
    diagnostics = query.all()
    
    # Формируем результат
    result = []
    for diag in diagnostics:
        # Получаем object_id из CSV (Object.object_id), а не внутренний ID
        csv_object_id = diag.object.object_id if diag.object else None
        
        result.append({
            "diag_id": diag.diag_id,
            "object_id": csv_object_id,  # Используем object_id из CSV для совместимости с frontend
            "method": diag.method.value,
            "date": diag.date.isoformat(),
            "temperature": diag.temperature,
            "humidity": diag.humidity,
            "illumination": diag.illumination,
            "defect_found": diag.defect_found,
            "defect_description": diag.defect_description,
            "quality_grade": diag.quality_grade.value if diag.quality_grade else None,
            "param1": diag.param1,
            "param2": diag.param2,
            "param3": diag.param3,
            "ml_label": diag.ml_label.value if diag.ml_label else None,
            "source_file": diag.source_file,
        })
    
    return result


@router.get("/diagnostics/{object_id}", response_model=List[DiagnosticListItem])
def get_diagnostics_for_object(
    object_id: int,
    include_probabilities: bool = False,
    session: Session = Depends(get_db),
):
    """
    Возвращает историю проверок для объекта.
    
    Использует object_id из CSV (не внутренний id).
    
    Args:
        object_id: ID объекта из CSV
        include_probabilities: Если True, возвращает вероятности ML предсказаний
    """
    # Находим объект по object_id (из CSV)
    obj = session.query(Object).filter(Object.object_id == object_id).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    # Получаем все диагностики для этого объекта
    diagnostics = (
        session.query(Diagnostic)
        .filter(Diagnostic.object_id == obj.id)
        .order_by(desc(Diagnostic.date))
        .all()
    )
    
    # Если нужны вероятности, вычисляем их для диагностик без ml_label
    ml_probabilities = {}
    if include_probabilities and ml_model and ml_model.is_trained:
        diagnostics_for_ml = [d for d in diagnostics if d.ml_label is None]
        if diagnostics_for_ml:
            try:
                ml_data = []
                for diag in diagnostics_for_ml:
                    ml_data.append({
                        "method": diag.method.value,
                        "param1": diag.param1 or 0.0,
                        "param2": diag.param2 or 0.0,
                        "defect_found": diag.defect_found,
                        "object_year": obj.year or 2000,
                    })
                
                ml_df = pd.DataFrame(ml_data)
                features = ml_model.prepare_features(ml_df)
                probabilities = ml_model.predict_proba(features)
                
                # Сохраняем вероятности
                for i, diag in enumerate(diagnostics_for_ml):
                    probs = probabilities[i]
                    ml_probabilities[diag.diag_id] = {
                        "normal": float(probs[0]) if len(probs) > 0 else 0.0,
                        "medium": float(probs[1]) if len(probs) > 1 else 0.0,
                        "high": float(probs[2]) if len(probs) > 2 else 0.0,
                    }
            except Exception as e:
                # В случае ошибки просто не возвращаем вероятности
                pass
    
    result = []
    for diag in diagnostics:
        diag_result = {
            "diag_id": diag.diag_id,
            "object_id": object_id,  # ID объекта из CSV (который был передан в URL)
            "method": diag.method.value,
            "date": diag.date.isoformat(),
            "temperature": diag.temperature,
            "humidity": diag.humidity,
            "illumination": diag.illumination,
            "defect_found": diag.defect_found,
            "defect_description": diag.defect_description,
            "quality_grade": diag.quality_grade.value if diag.quality_grade else None,
            "param1": diag.param1,
            "param2": diag.param2,
            "param3": diag.param3,
            "ml_label": diag.ml_label.value if diag.ml_label else None,
            "source_file": diag.source_file,
        }
        
        # Добавляем вероятности, если запрошены
        if include_probabilities:
            if diag.diag_id in ml_probabilities:
                diag_result["ml_probabilities"] = ml_probabilities[diag.diag_id]
            elif diag.ml_label:
                # Для диагностик с уже установленным ml_label, возвращаем вероятности 1.0 для соответствующего класса
                label = diag.ml_label.value
                diag_result["ml_probabilities"] = {
                    "normal": 1.0 if label == "normal" else 0.0,
                    "medium": 1.0 if label == "medium" else 0.0,
                    "high": 1.0 if label == "high" else 0.0,
                }
        
        result.append(diag_result)
    
    return result


@router.post("/diagnostics/mark-fixed/{object_id}", response_model=Dict)
def mark_defect_as_fixed(
    object_id: int,
    method: DiagnosticMethod = DiagnosticMethod.VIK,
    diagnostic_date: Optional[date] = None,
    defect_description: Optional[str] = "Дефект устранен после ремонта",
    quality_grade: Optional[QualityGrade] = QualityGrade.УДОВЛЕТВОРИТЕЛЬНО,
    param1: Optional[float] = None,
    param2: Optional[float] = None,
    param3: Optional[float] = None,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    illumination: Optional[float] = None,
    session: Session = Depends(get_db),
):
    """
    Создает отчет об исправлении дефекта для объекта.
    
    Автоматически создает новую диагностику с defect_found=False,
    что обновит статус объекта на карте и в таблице.
    
    Args:
        object_id: ID объекта из CSV (не внутренний id)
        method: Метод диагностики (по умолчанию VIK)
        diagnostic_date: Дата диагностики (по умолчанию сегодня)
        defect_description: Описание (по умолчанию "Дефект устранен после ремонта")
        quality_grade: Оценка качества
        param1, param2, param3: Параметры диагностики
        temperature, humidity, illumination: Условия диагностики
    """
    # Находим объект по object_id (из CSV)
    obj = session.query(Object).filter(Object.object_id == object_id).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail=f"Object with object_id={object_id} not found")
    
    # Проверяем, есть ли у объекта критический дефект
    last_diag = (
        session.query(Diagnostic)
        .filter(Diagnostic.object_id == obj.id)
        .order_by(desc(Diagnostic.date))
        .first()
    )
    
    if not last_diag:
        raise HTTPException(
            status_code=400,
            detail=f"Object {object_id} has no diagnostics. Cannot mark as fixed."
        )
    
    if not last_diag.defect_found:
        return {
            "message": f"Object {object_id} already has no active defects",
            "object_id": object_id,
            "current_status": "Normal",
            "last_diagnostic_date": last_diag.date.isoformat(),
        }
    
    # Используем сегодняшнюю дату, если не указана
    if diagnostic_date is None:
        diagnostic_date = date.today()
    
    # Определяем ML метку (normal, так как дефекта нет)
    ml_label = MLLabel.NORMAL
    
    # Создаем новую диагностику с defect_found=False
    new_diagnostic = Diagnostic(
        object_id=obj.id,
        method=method,
        date=diagnostic_date,
        temperature=temperature,
        humidity=humidity,
        illumination=illumination,
        defect_found=False,  # Ключевой параметр - дефект устранен
        defect_description=defect_description,
        quality_grade=quality_grade,
        param1=param1,
        param2=param2,
        param3=param3,
        ml_label=ml_label,
        source_file="MANUAL_FIX_REPORT",
    )
    
    session.add(new_diagnostic)
    session.commit()
    session.refresh(new_diagnostic)
    
    return {
        "message": f"Defect marked as fixed for object {object_id}",
        "object_id": object_id,
        "object_name": obj.object_name,
        "new_status": "Normal",
        "previous_status": "Critical",
        "diagnostic_id": new_diagnostic.diag_id,
        "diagnostic_date": diagnostic_date.isoformat(),
        "method": method.value,
    }
