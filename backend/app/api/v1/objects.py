"""
API endpoints для объектов.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc, func, case, and_, or_, cast, String, text
from typing import List, Optional
from datetime import date as date_type

from app.core.database import get_db
from app.models.object import Object
from app.models.diagnostic import Diagnostic, DiagnosticMethod, MLLabel
from app.schemas.object import ObjectListItem

router = APIRouter()


@router.get("/objects/test")
def test_objects(session: Session = Depends(get_db)):
    """Тестовый endpoint для проверки работы API."""
    return {"message": "API работает", "count": session.query(Object).count()}


@router.get("/objects", response_model=List[ObjectListItem])
def get_objects(
    session: Session = Depends(get_db),
    pipeline_id: Optional[str] = Query(None, description="Фильтр по ID трубопровода (MT-01, MT-02, etc.)"),
    method: Optional[str] = Query(None, description="Фильтр по методу диагностики"),
    risk_level: Optional[str] = Query(None, description="Фильтр по уровню риска (normal/medium/high)"),
    date_from: Optional[date_type] = Query(None, description="Фильтр: дата диагностики от"),
    date_to: Optional[date_type] = Query(None, description="Фильтр: дата диагностики до"),
    param1_min: Optional[float] = Query(None, description="Минимальное значение param1"),
    param1_max: Optional[float] = Query(None, description="Максимальное значение param1"),
    param2_min: Optional[float] = Query(None, description="Минимальное значение param2"),
    param2_max: Optional[float] = Query(None, description="Максимальное значение param2"),
    param3_min: Optional[float] = Query(None, description="Минимальное значение param3"),
    param3_max: Optional[float] = Query(None, description="Максимальное значение param3"),
    sort_by: Optional[str] = Query(None, description="Сортировка: param1, param2, param3, date"),
    sort_order: Optional[str] = Query("asc", description="Порядок сортировки: asc или desc"),
):
    """
    Возвращает список всех объектов с фильтрацией и сортировкой.
    
    Статус (Critical/Normal) вычисляется на основе наличия дефектов.
    
    Поддерживает фильтрацию по:
    - pipeline_id: ID трубопровода
    - method: Метод диагностики
    - risk_level: Уровень риска (normal/medium/high)
    - date_from/date_to: Диапазон дат диагностики
    - param1_min/max, param2_min/max, param3_min/max: Диапазоны параметров
    - sort_by: Поле для сортировки (param1, param2, param3, date)
    - sort_order: Порядок сортировки (asc/desc)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Обрабатываем Query объекты (FastAPI передает их при прямом вызове, но при HTTP запросе заменяет на фактические значения)
    def get_value(param):
        """Извлекает значение из Query объекта или возвращает параметр как есть."""
        # Проверяем, является ли это Query объектом через строковое представление
        if param is not None and hasattr(param, 'default'):
            param_str = str(type(param).__name__)
            if 'Query' in param_str:
                # Для Query объектов получаем default значение
                return param.default if hasattr(param, 'default') else None
        return param
    
    # Извлекаем фактические значения из параметров
    pipeline_id = get_value(pipeline_id)
    method = get_value(method)
    risk_level = get_value(risk_level)
    date_from = get_value(date_from)
    date_to = get_value(date_to)
    param1_min = get_value(param1_min)
    param1_max = get_value(param1_max)
    param2_min = get_value(param2_min)
    param2_max = get_value(param2_max)
    param3_min = get_value(param3_min)
    param3_max = get_value(param3_max)
    sort_by = get_value(sort_by)
    sort_order = get_value(sort_order) or "asc"
    
    # Базовый запрос объектов (без eager loading для производительности)
    query = session.query(Object)
    
    # Важно: исключаем объекты без валидных координат из отображения на карте
    # Объекты с location_status=PENDING или координатами None не показываются на карте
    # Они остаются в БД для последующего обновления координат
    # Фильтруем по координатам (location_status проверим после загрузки через SQL)
    query = query.filter(
        and_(
            Object.lat.isnot(None),
            Object.lon.isnot(None)
        )
    )
    
    # Фильтрация по pipeline_id
    if pipeline_id:
        from app.models.pipeline import Pipeline
        pipeline = session.query(Pipeline).filter(Pipeline.name == str(pipeline_id)).first()
        if pipeline:
            query = query.filter(Object.pipeline_id == pipeline.id)
        else:
            # Если pipeline не найден, возвращаем пустой список
            return []
    
    # Фильтрация по методу, дате, параметрам и risk_level требует подзапроса
    # Создаем подзапрос для фильтрации по диагностикам
    diagnostic_filters = []
    
    if method:
        try:
            method_enum = DiagnosticMethod(str(method).upper())
            diagnostic_filters.append(Diagnostic.method == method_enum)
        except (ValueError, AttributeError):
            pass  # Неверный метод, игнорируем
    
    if risk_level:
        try:
            risk_enum = MLLabel(str(risk_level).lower())
            diagnostic_filters.append(Diagnostic.ml_label == risk_enum)
        except (ValueError, AttributeError):
            pass
    
    if date_from and isinstance(date_from, date_type):
        diagnostic_filters.append(Diagnostic.date >= date_from)
    
    if date_to and isinstance(date_to, date_type):
        diagnostic_filters.append(Diagnostic.date <= date_to)
    
    if param1_min is not None and isinstance(param1_min, (int, float)):
        diagnostic_filters.append(Diagnostic.param1 >= param1_min)
    
    if param1_max is not None and isinstance(param1_max, (int, float)):
        diagnostic_filters.append(Diagnostic.param1 <= param1_max)
    
    if param2_min is not None and isinstance(param2_min, (int, float)):
        diagnostic_filters.append(Diagnostic.param2 >= param2_min)
    
    if param2_max is not None and isinstance(param2_max, (int, float)):
        diagnostic_filters.append(Diagnostic.param2 <= param2_max)
    
    if param3_min is not None and isinstance(param3_min, (int, float)):
        diagnostic_filters.append(Diagnostic.param3 >= param3_min)
    
    if param3_max is not None and isinstance(param3_max, (int, float)):
        diagnostic_filters.append(Diagnostic.param3 <= param3_max)
    
    # Если есть фильтры по диагностикам, применяем их
    if diagnostic_filters:
        # Получаем ID объектов, которые соответствуют фильтрам
        try:
            filtered_object_ids = session.query(Diagnostic.object_id).filter(
                and_(*diagnostic_filters)
            ).distinct().all()
            filtered_object_ids = [row[0] for row in filtered_object_ids if row[0] is not None]
            if filtered_object_ids:
                query = query.filter(Object.id.in_(filtered_object_ids))
            else:
                # Если нет объектов, соответствующих фильтрам, возвращаем пустой список
                return []
        except Exception as e:
            # В случае ошибки логируем и возвращаем пустой список
            import logging
            logging.error(f"Ошибка при фильтрации по диагностикам: {e}")
            return []
    
    # Получаем объекты (без eager loading pipeline для начала)
    # Загружаем объекты с валидными координатами
    objects = query.all()
    object_ids = [obj.id for obj in objects]
    
    if not object_ids:
        return []
    
    # Получаем location_status через прямой SQL запрос (избегаем проблем с enum)
    # и фильтруем объекты с verified статусом
    # Используем прямую передачу параметров для SQLite
    if object_ids:
        # Создаем параметры для IN clause
        params = {f'id{i}': obj_id for i, obj_id in enumerate(object_ids)}
        placeholders = ','.join([f':id{i}' for i in range(len(object_ids))])
        status_result = session.execute(
            text(f"SELECT id, location_status FROM objects WHERE id IN ({placeholders})"),
            params
        ).fetchall()
    else:
        status_result = []
    
    # Создаем маппинг и фильтруем только verified объекты
    object_location_status_map = {}
    verified_object_ids = set()
    for row in status_result:
        obj_id, status = row[0], row[1]
        object_location_status_map[obj_id] = status
        if status == 'verified':
            verified_object_ids.add(obj_id)
    
    # Фильтруем объекты - оставляем только с verified статусом
    objects = [obj for obj in objects if obj.id in verified_object_ids]
    object_ids = [obj.id for obj in objects]
    
    if not object_ids:
        return []
    
    # Загружаем последние диагностики для всех объектов (нужно для определения статуса и сортировки)
    # ВАЖНО: Для наряда-допуска важен только статус ПОСЛЕДНЕЙ диагностики, а не вся история
    logger.info("Загружаем последние диагностики для определения статуса объектов")
    last_diagnostics = {}
    try:
        if object_ids:
            # Простой и надежный способ: загружаем диагностики с сортировкой и берем первую для каждого объекта
            # Используем limit для безопасности - максимум 50000 диагностик
            all_diagnostics = (
                session.query(Diagnostic)
                .filter(Diagnostic.object_id.in_(object_ids))
                .order_by(Diagnostic.object_id, desc(Diagnostic.date))
                .limit(50000)
                .all()
            )
            
            # Группируем по object_id и берем первую (последнюю по дате) для каждого объекта
            for diag in all_diagnostics:
                if diag.object_id not in last_diagnostics:
                    last_diagnostics[diag.object_id] = diag
                    
            logger.info(f"Загружено последних диагностик: {len(last_diagnostics)} из {len(object_ids)} объектов")
    except Exception as e:
        import logging
        logging.warning(f"Ошибка при загрузке диагностик: {e}")
        last_diagnostics = {}
    
    # Определяем объекты с дефектами только по ПОСЛЕДНЕЙ диагностике
    # Это важно для наряда-допуска - учитываем актуальное состояние, а не историю
    objects_with_defects = {
        obj_id for obj_id, diag in last_diagnostics.items()
        if diag and diag.defect_found == True
    }
    logger.info(f"Найдено объектов с дефектами в последней диагностике: {len(objects_with_defects)}")
    
    # Загружаем все pipeline одним запросом для избежания N+1
    from app.models.pipeline import Pipeline
    pipeline_ids = {obj.pipeline_id for obj in objects}
    pipelines = {p.id: p for p in session.query(Pipeline).filter(Pipeline.id.in_(pipeline_ids)).all()}
    
    # Формируем результат с дополнительной информацией для сортировки
    result_data = []
    for obj in objects:
        has_defect = obj.id in objects_with_defects
        status = "Critical" if has_defect else "Normal"
        
        # Получаем последнюю диагностику из кэша
        last_diag = last_diagnostics.get(obj.id)
        
        # Получаем location_status из маппинга (загружен как строка) или пытаемся из объекта
        try:
            location_status_value = object_location_status_map.get(obj.id)
            if location_status_value is None:
                # Пытаемся получить из объекта, но обрабатываем ошибку enum
                try:
                    location_status_value = obj.location_status.value if hasattr(obj.location_status, 'value') else str(obj.location_status)
                except (AttributeError, LookupError):
                    location_status_value = None
        except Exception:
            location_status_value = None
        
        # Получаем risk_level из ml_label последней диагностики
        risk_level = None
        if last_diag and last_diag.ml_label:
            risk_level = last_diag.ml_label.value if hasattr(last_diag.ml_label, 'value') else str(last_diag.ml_label)
        
        result_data.append({
            "id": obj.object_id,
            "name": obj.object_name,
            "type": obj.object_type.value,
            "lat": obj.lat,
            "lon": obj.lon,
            "status": status,
            "pipeline_id": pipelines.get(obj.pipeline_id).name if pipelines.get(obj.pipeline_id) else None,
            "location_status": location_status_value,
            "risk_level": risk_level,
            "_sort_param1": last_diag.param1 if last_diag and last_diag.param1 else 0,
            "_sort_param2": last_diag.param2 if last_diag and last_diag.param2 else 0,
            "_sort_param3": last_diag.param3 if last_diag and last_diag.param3 else 0,
            "_sort_date": last_diag.date if last_diag else date_type(1900, 1, 1),
        })
    
    # Сортировка
    if sort_by:
        sort_order_str = str(sort_order) if sort_order else "asc"
        reverse = sort_order_str.lower() == "desc"
        if sort_by == "param1":
            result_data.sort(key=lambda x: x["_sort_param1"], reverse=reverse)
        elif sort_by == "param2":
            result_data.sort(key=lambda x: x["_sort_param2"], reverse=reverse)
        elif sort_by == "param3":
            result_data.sort(key=lambda x: x["_sort_param3"], reverse=reverse)
        elif sort_by == "date":
            result_data.sort(key=lambda x: x["_sort_date"], reverse=reverse)
    
    # Удаляем служебные поля перед возвратом
    result = []
    for item in result_data:
        result.append({
            "id": item["id"],
            "name": item["name"],
            "type": item["type"],
            "lat": item["lat"],
            "lon": item["lon"],
            "status": item["status"],
            "pipeline_id": item["pipeline_id"],
            "location_status": item.get("location_status"),
            "risk_level": item.get("risk_level"),
        })
    
    logger.info(f"Возвращаем {len(result)} объектов")
    return result
