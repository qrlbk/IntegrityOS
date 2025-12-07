"""
API endpoints для аналитики и статистики.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, desc
from typing import List, Dict

from app.core.database import get_db
from app.models.diagnostic import Diagnostic, MLLabel
from app.models.object import Object
from app.schemas.analytics import DefectsTimelineItem

router = APIRouter()


@router.get("/analytics/defects-timeline", response_model=List[DefectsTimelineItem])
def get_defects_timeline(
    session: Session = Depends(get_db),
):
    """
    Возвращает динамику дефектов по годам для графика.
    """
    # Получаем количество дефектов по годам
    # В SQLite используем CASE для преобразования boolean в integer
    from sqlalchemy import case
    
    defects_by_year = (
        session.query(
            extract('year', Diagnostic.date).label('year'),
            func.count(Diagnostic.diag_id).label('total'),
            func.sum(
                case((Diagnostic.defect_found == True, 1), else_=0)
            ).label('defects')
        )
        .group_by(extract('year', Diagnostic.date))
        .order_by(extract('year', Diagnostic.date))
        .all()
    )
    
    result = []
    for year, total, defects in defects_by_year:
        result.append({
            "year": int(year) if year else 2024,
            "total": total or 0,
            "defects": int(defects) if defects else 0,
            "percentage": round((int(defects) / total * 100) if total > 0 else 0, 2)
        })
    
    return result


@router.get("/analytics/top-risks")
def get_top_risks(
    session: Session = Depends(get_db),
    limit: int = 5,
):
    """
    Возвращает топ-N объектов с наибольшим количеством критических дефектов.
    """
    try:
        # Подсчитываем количество дефектов high для каждого объекта
        risks = (
            session.query(
                Object.object_id,
                Object.object_name,
                Object.object_type,
                Object.lat,
                Object.lon,
                func.count(Diagnostic.diag_id).label('high_count')
            )
            .join(Diagnostic, Diagnostic.object_id == Object.id)
            .filter(Diagnostic.ml_label == MLLabel.HIGH)
            .group_by(Object.id, Object.object_id, Object.object_name, Object.object_type, Object.lat, Object.lon)
            .order_by(desc('high_count'))
            .limit(limit)
            .all()
        )
        
        result = []
        for obj_id, name, obj_type, lat, lon, high_count in risks:
            try:
                obj_type_str = obj_type.value if hasattr(obj_type, 'value') else str(obj_type)
            except:
                obj_type_str = str(obj_type)
            
            result.append({
                "object_id": obj_id,
                "object_name": name,
                "object_type": obj_type_str,
                "lat": lat,
                "lon": lon,
                "high_defects_count": int(high_count) if high_count else 0,
            })
        
        return result
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении топ-рисков: {e}", exc_info=True)
        # Возвращаем пустой список вместо ошибки
        return []


@router.get("/analytics/methods-distribution")
def get_methods_distribution(
    session: Session = Depends(get_db),
):
    """
    Возвращает распределение дефектов по методам диагностики.
    """
    try:
        distribution = (
            session.query(
                Diagnostic.method,
                func.count(Diagnostic.diag_id).label('total'),
                func.sum(
                    case((Diagnostic.defect_found == True, 1), else_=0)
                ).label('defects')
            )
            .group_by(Diagnostic.method)
            .all()
        )
        
        result = []
        for method, total, defects in distribution:
            try:
                # Пытаемся получить значение enum
                if hasattr(method, 'value'):
                    method_str = method.value
                elif isinstance(method, str):
                    method_str = method
                else:
                    method_str = str(method)
            except Exception:
                # Если не получается, используем строковое представление
                method_str = str(method) if method else "UNKNOWN"
            
            result.append({
                "method": method_str,
                "total": int(total) if total else 0,
                "defects": int(defects) if defects else 0,
                "percentage": round((int(defects) / total * 100) if total > 0 else 0, 2)
            })
        
        return result
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении распределения по методам: {e}", exc_info=True)
        # Возвращаем пустой список вместо ошибки
        return []


@router.get("/analytics/criticality-distribution")
def get_criticality_distribution(
    session: Session = Depends(get_db),
):
    """
    Возвращает распределение дефектов по критичности (ml_label).
    """
    try:
        distribution = (
            session.query(
                Diagnostic.ml_label,
                func.count(Diagnostic.diag_id).label('count')
            )
            .filter(Diagnostic.ml_label.isnot(None))
            .group_by(Diagnostic.ml_label)
            .all()
        )
        
        total = sum(count for _, count in distribution)
        
        result = []
        for label, count in distribution:
            try:
                label_str = label.value if hasattr(label, 'value') else str(label)
            except:
                label_str = str(label)
            
            result.append({
                "label": label_str,
                "count": int(count) if count else 0,
                "percentage": round((int(count) / total * 100) if total > 0 else 0, 2)
            })
        
        return result
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении распределения по критичности: {e}", exc_info=True)
        # Возвращаем пустой список вместо ошибки
        return []


@router.get("/analytics/stats-summary")
def get_stats_summary(
    session: Session = Depends(get_db),
):
    """
    Возвращает общую статистику для дашборда.
    """
    try:
        from datetime import datetime, timedelta
        
        total_objects = session.query(func.count(Object.id)).scalar() or 0
        total_diagnostics = session.query(func.count(Diagnostic.diag_id)).scalar() or 0
        
        # Дефекты
        total_defects = (
            session.query(func.count(Diagnostic.diag_id))
            .filter(Diagnostic.defect_found == True)
            .scalar() or 0
        )
        
        # Активные дефекты (дефекты с ml_label HIGH или MEDIUM)
        active_defects = (
            session.query(func.count(Diagnostic.diag_id))
            .filter(
                Diagnostic.defect_found == True,
                Diagnostic.ml_label.in_([MLLabel.HIGH, MLLabel.MEDIUM])
            )
            .scalar() or 0
        )
        
        # Критичность
        try:
            high_count = (
                session.query(func.count(Diagnostic.diag_id))
                .filter(Diagnostic.ml_label == MLLabel.HIGH)
                .scalar() or 0
            )
        except:
            high_count = 0
        
        try:
            medium_count = (
                session.query(func.count(Diagnostic.diag_id))
                .filter(Diagnostic.ml_label == MLLabel.MEDIUM)
                .scalar() or 0
            )
        except:
            medium_count = 0
        
        try:
            normal_count = (
                session.query(func.count(Diagnostic.diag_id))
                .filter(Diagnostic.ml_label == MLLabel.NORMAL)
                .scalar() or 0
            )
        except:
            normal_count = 0
        
        # Ремонты за год (дефекты со статусом "исправлен" или quality_grade "удовлетворительно")
        # Используем текущий год
        current_year = datetime.now().year
        repairs_this_year = (
            session.query(func.count(Diagnostic.diag_id))
            .filter(
                extract('year', Diagnostic.date) == current_year,
                Diagnostic.defect_found == False  # Исправленные дефекты
            )
            .scalar() or 0
        )
        
        # Тренды (сравнение с предыдущим периодом)
        # Для упрощения считаем тренд как изменение за последние 30 дней
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        
        # Дефекты за последние 30 дней
        recent_defects = (
            session.query(func.count(Diagnostic.diag_id))
            .filter(
                Diagnostic.date >= thirty_days_ago,
                Diagnostic.defect_found == True
            )
            .scalar() or 0
        )
        
        # Дефекты за предыдущие 30 дней (60-30 дней назад)
        sixty_days_ago = datetime.now().date() - timedelta(days=60)
        previous_defects = (
            session.query(func.count(Diagnostic.diag_id))
            .filter(
                Diagnostic.date >= sixty_days_ago,
                Diagnostic.date < thirty_days_ago,
                Diagnostic.defect_found == True
            )
            .scalar() or 0
        )
        
        # Расчет тренда для дефектов
        defects_trend = None
        defects_trend_value = None
        if previous_defects > 0:
            change = ((recent_defects - previous_defects) / previous_defects) * 100
            defects_trend = "up" if change > 0 else "down"
            defects_trend_value = f"{abs(change):.1f}%"
        elif recent_defects > 0:
            defects_trend = "up"
            defects_trend_value = "100%"
        
        # Тренд для диагностик
        recent_diagnostics = (
            session.query(func.count(Diagnostic.diag_id))
            .filter(Diagnostic.date >= thirty_days_ago)
            .scalar() or 0
        )
        
        previous_diagnostics = (
            session.query(func.count(Diagnostic.diag_id))
            .filter(
                Diagnostic.date >= sixty_days_ago,
                Diagnostic.date < thirty_days_ago
            )
            .scalar() or 0
        )
        
        diagnostics_trend = None
        diagnostics_trend_value = None
        if previous_diagnostics > 0:
            change = ((recent_diagnostics - previous_diagnostics) / previous_diagnostics) * 100
            diagnostics_trend = "up" if change > 0 else "down"
            diagnostics_trend_value = f"{abs(change):.1f}%"
        elif recent_diagnostics > 0:
            diagnostics_trend = "up"
            diagnostics_trend_value = "100%"
        
        return {
            "total_objects": total_objects,
            "total_diagnostics": total_diagnostics,
            "total_defects": total_defects,
            "active_defects": active_defects,
            "defects_percentage": round((total_defects / total_diagnostics * 100) if total_diagnostics > 0 else 0, 2),
            "repairs_this_year": repairs_this_year,
            "criticality": {
                "high": high_count,
                "medium": medium_count,
                "normal": normal_count,
            },
            "trends": {
                "defects": {
                    "direction": defects_trend,
                    "value": defects_trend_value,
                },
                "diagnostics": {
                    "direction": diagnostics_trend,
                    "value": diagnostics_trend_value,
                }
            }
        }
    except Exception as e:
        import logging
        logging.error(f"Ошибка при получении статистики: {e}", exc_info=True)
        # Возвращаем пустую статистику вместо ошибки
        return {
            "total_objects": 0,
            "total_diagnostics": 0,
            "total_defects": 0,
            "active_defects": 0,
            "defects_percentage": 0,
            "repairs_this_year": 0,
            "criticality": {
                "high": 0,
                "medium": 0,
                "normal": 0,
            },
            "trends": {
                "defects": {
                    "direction": None,
                    "value": None,
                },
                "diagnostics": {
                    "direction": None,
                    "value": None,
                }
            }
        }

