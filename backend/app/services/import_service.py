"""
Сервис для импорта CSV файлов из локальной папки data/.
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.object import Object, ObjectType, LocationStatus
from app.models.diagnostic import Diagnostic, DiagnosticMethod, MLLabel, QualityGrade
from app.models.pipeline import Pipeline
from app.core.ml_model import ml_model
from app.core.logging_config import logger


def _determine_criticality_by_rules(
    defect_found: bool,
    defect_description: str,
    param1: float,
    param2: float,
    param3: float,
    method: str,
) -> str:
    """
    Правило-основанная логика для определения критичности дефекта.
    
    Args:
        defect_found: Найден ли дефект
        defect_description: Описание дефекта
        param1: Параметр 1 (например, глубина коррозии)
        param2: Параметр 2 (например, площадь дефекта)
        param3: Параметр 3 (дополнительный параметр)
        method: Метод диагностики
        
    Returns:
        "normal", "medium" или "high"
    """
    # Если дефект не найден - норма
    if not defect_found:
        return "normal"
    
    # Анализируем описание дефекта
    desc_lower = defect_description.lower()
    
    # Критические ключевые слова
    critical_keywords = [
        "критический", "критично", "аварийный", "авария",
        "разрушение", "разрыв", "трещина сквозная", "сквозная",
        "глубокая коррозия", "сильная коррозия", "обширная",
    ]
    
    # Средние ключевые слова
    medium_keywords = [
        "коррозия", "повреждение", "дефект", "трещина",
        "износ", "изношен", "поврежден",
    ]
    
    # Проверяем критические признаки
    is_critical = any(keyword in desc_lower for keyword in critical_keywords)
    is_medium = any(keyword in desc_lower for keyword in medium_keywords)
    
    # Анализируем параметры
    # param1 обычно глубина/размер дефекта
    # param2 обычно площадь/протяженность
    # param3 дополнительный параметр
    
    # Критические пороги (зависит от метода, но общие правила)
    critical_param1_threshold = 20.0  # мм для коррозии
    critical_param2_threshold = 50.0  # % площади
    medium_param1_threshold = 10.0
    medium_param2_threshold = 20.0
    
    # Определяем критичность на основе параметров
    param_criticality = "normal"
    
    if param1 >= critical_param1_threshold or param2 >= critical_param2_threshold:
        param_criticality = "high"
    elif param1 >= medium_param1_threshold or param2 >= medium_param2_threshold:
        param_criticality = "medium"
    
    # Комбинируем анализ описания и параметров
    if is_critical or param_criticality == "high":
        return "high"
    elif is_medium or param_criticality == "medium":
        return "medium"
    else:
        return "normal"


def _train_model_sync(session: Session) -> Dict:
    """
    Синхронная версия обучения модели на размеченных данных из БД.
    
    Args:
        session: DB сессия
        
    Returns:
        Статистика обучения
    """
    try:
        from app.core.config import settings
        
        # Получаем размеченные данные
        labeled_diagnostics = (
            session.query(Diagnostic, Object.year)
            .join(Object, Diagnostic.object_id == Object.id)
            .filter(Diagnostic.ml_label.isnot(None))
            .all()
        )
        
        min_samples = settings.ML_MIN_SAMPLES_FOR_TRAINING
        if len(labeled_diagnostics) < min_samples:
            logger.info(f"Недостаточно данных для обучения. Нужно минимум {min_samples}, получено {len(labeled_diagnostics)}")
            return {
                "trained": False,
                "samples": len(labeled_diagnostics),
            }
        
        # Подготавливаем данные
        data = []
        for diagnostic, year in labeled_diagnostics:
            data.append({
                "param1": diagnostic.param1 or 0,
                "param2": diagnostic.param2 or 0,
                "method": diagnostic.method.value,
                "defect_found": diagnostic.defect_found,
                "object_year": year or 2000,
                "ml_label": diagnostic.ml_label.value,
            })
        
        df = pd.DataFrame(data)
        
        # Подготавливаем признаки и метки
        X = df.drop(columns=["ml_label"])
        y = df["ml_label"].values
        
        # Обучаем модель с метриками
        result = ml_model.train(X, y, use_mlflow=True)
        
        logger.info(f"✅ ML модель успешно обучена на {len(labeled_diagnostics)} записях")
        return {
            "trained": True,
            "samples": len(labeled_diagnostics),
        }
    except Exception as e:
        logger.error(f"Ошибка при обучении модели: {e}", exc_info=True)
        return {
            "trained": False,
            "error": str(e),
        }


def _read_data_file(file_path: Path) -> pd.DataFrame:
    """
    Читает файл данных (CSV или XLSX).
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        DataFrame с данными
    """
    file_ext = file_path.suffix.lower()
    if file_ext == '.xlsx' or file_ext == '.xls':
        logger.info(f"Чтение XLSX файла: {file_path}")
        return pd.read_excel(file_path)
    else:
        logger.info(f"Чтение CSV файла: {file_path}")
        return pd.read_csv(file_path)


def import_data_from_csv(
    session: Session,
    diagnostics_csv_path: Path,
    objects_csv_path: Path = None,
    clear_existing: bool = True,
) -> Dict:
    """
    Импорт данных из CSV/XLSX файлов.
    
    Если objects_csv_path не указан, система автоматически создаст объекты из Diagnostics.
    Это упрощает процесс - сотрудник может отправить только отчет о диагностике,
    а AI/ML система автоматически создаст объекты и проанализирует данные.
    
    Args:
        session: DB сессия
        diagnostics_csv_path: Путь к Diagnostics.csv/xlsx (обязательно)
        objects_csv_path: Путь к Objects.csv/xlsx (опционально - если None, объекты создаются автоматически)
        clear_existing: Если True, очищает существующие данные
        
    Returns:
        Статистика импорта
    """
    errors = []
    auto_created_objects = 0
    
    try:
        # Начинаем транзакцию
        # Очистка существующих данных (если нужно)
        if clear_existing:
            logger.info("Очистка существующих данных...")
            session.execute(delete(Diagnostic))
            session.execute(delete(Object))
            session.execute(delete(Pipeline))
            # Не коммитим здесь, все в одной транзакции
        
        # Читаем Diagnostics для получения object_id (нужно в любом случае)
        logger.info("Чтение файла Diagnostics...")
        diagnostics_df = _read_data_file(diagnostics_csv_path)
        
        # Если Objects файл не указан, создаем объекты автоматически из Diagnostics
        if objects_csv_path is None:
            logger.info("Файл Objects не указан. Автоматическое создание объектов из Diagnostics...")
            
            # Получаем уникальные object_id из Diagnostics
            unique_object_ids = diagnostics_df["object_id"].dropna().unique()
            
            # Получаем существующие объекты
            existing_object_ids = set()
            if not clear_existing:
                existing_objects = session.query(Object.object_id).all()
                existing_object_ids = {row[0] for row in existing_objects}
            
            # Создаем Pipeline для автоматически созданных объектов
            default_pipeline_name = "AUTO-CREATED"
            default_pipeline = session.query(Pipeline).filter(Pipeline.name == default_pipeline_name).first()
            if not default_pipeline:
                default_pipeline = Pipeline(name=default_pipeline_name)
                session.add(default_pipeline)
                session.flush()
            
            # Создаем объекты, которых нет
            new_objects = []
            for obj_id in unique_object_ids:
                try:
                    obj_id_int = int(obj_id)
        
                    # Пропускаем существующие
                    if obj_id_int in existing_object_ids:
                        continue
                    
                    # Создаем минимальный объект - координаты устанавливаем в None
                    # Координаты (None, None) означают, что объект существует в системе,
                    # но еще не имеет реальных координат и не будет показываться на карте
                    # до тех пор, пока координаты не будут установлены
                    obj = Object(
                        object_id=obj_id_int,
                        object_name=f"Объект-{obj_id_int}",  # AI может улучшить имя позже
                        object_type=ObjectType.PIPELINE_SECTION,  # Дефолтный тип
                        pipeline_id=default_pipeline.id,
                        lat=None,  # None означает координаты не установлены - объект не будет на карте
                        lon=None,  # None означает координаты не установлены - объект не будет на карте
                        location_status=LocationStatus.PENDING,  # Статус: ожидает установки координат
                        year=None,
                        material=None,
                    )
                    new_objects.append(obj)
                except Exception as e:
                    errors.append(f"Ошибка создания объекта {obj_id}: {str(e)}")
            
            if new_objects:
                logger.info(f"✨ Автоматически создано {len(new_objects)} объектов из Diagnostics (AI/ML проанализирует данные)...")
                session.add_all(new_objects)
                session.flush()
                auto_created_objects = len(new_objects)
            
            # Создаем пустой DataFrame для совместимости с остальным кодом
            objects_df = pd.DataFrame(columns=["object_id", "pipeline_id"])
        else:
            # 1. Импорт Pipeline (автоматически из pipeline_id в Objects.csv)
            logger.info("Чтение файла Objects...")
            objects_df = _read_data_file(objects_csv_path)
        
        # Создаем или получаем Pipeline записи (если есть данные в Objects)
        pipeline_map = {}  # pipeline_id -> Pipeline объект
        
        if not objects_df.empty and "pipeline_id" in objects_df.columns:
            unique_pipelines = objects_df["pipeline_id"].unique()
            
        for pipeline_name in unique_pipelines:
            pipeline_name = str(pipeline_name).strip()
            if not pipeline_name:
                continue
            
            # Проверяем существование
            existing = session.query(Pipeline).filter(Pipeline.name == pipeline_name).first()
            if existing:
                pipeline_map[pipeline_name] = existing
            else:
                pipeline = Pipeline(name=pipeline_name)
                session.add(pipeline)
                session.flush()  # Получаем ID без коммита
                pipeline_map[pipeline_name] = pipeline
        
        # 2. Импорт Objects (если файл был указан)
        # Получаем существующие object_id для проверки дубликатов
        existing_object_ids = set()
        if not clear_existing:
            existing_objects = session.query(Object.object_id).all()
            existing_object_ids = {row[0] for row in existing_objects}
        
        objects = []
        skipped_objects = 0
        
        # Импортируем объекты только если файл был указан
        if objects_csv_path is not None and not objects_df.empty:
            for idx, row in objects_df.iterrows():
                try:
                    csv_object_id = int(row["object_id"])
                    
                    # Проверяем дубликаты, если не очищаем существующие данные
                    if not clear_existing and csv_object_id in existing_object_ids:
                        skipped_objects += 1
                        continue  # Пропускаем существующий объект
                    
                    pipeline_name = str(row["pipeline_id"]).strip()
                    pipeline = pipeline_map.get(pipeline_name)
                    if not pipeline:
                        errors.append(f"Строка {idx + 2}: pipeline_id '{pipeline_name}' не найден")
                        continue
                    
                    object_type_str = str(row["object_type"]).lower()
                    if object_type_str not in ["crane", "compressor", "pipeline_section"]:
                        errors.append(f"Строка {idx + 2}: неверный object_type '{row['object_type']}'")
                        continue
                    
                    obj = Object(
                        object_id=csv_object_id,
                        object_name=str(row["object_name"]),
                        object_type=ObjectType(object_type_str),
                        pipeline_id=pipeline.id,
                        lat=float(row["lat"]),
                        lon=float(row["lon"]),
                        year=int(row["year"]) if pd.notna(row.get("year")) else None,
                        material=str(row["material"]) if pd.notna(row.get("material")) else None,
                    )
                    objects.append(obj)
                except Exception as e:
                    errors.append(f"Строка {idx + 2}: {str(e)}")
        
        # Получаем маппинг для всех объектов (новых и существующих)
        object_id_map = {}
        db_objects = []
        
        if objects:
            logger.info(f"Импорт {len(objects)} новых объектов (пропущено дубликатов: {skipped_objects})...")
            session.add_all(objects)
            session.flush()  # Получаем ID без коммита
        
        # Получаем все объекты (новые + существующие) для маппинга
        all_csv_object_ids = set()
        
        # Если был файл Objects, собираем object_id из него
        if objects_csv_path is not None and not objects_df.empty:
            for _, row in objects_df.iterrows():
                try:
                    all_csv_object_ids.add(int(row["object_id"]))
                except:
                    pass
        
        # Если не очищаем существующие, добавляем существующие object_id для маппинга
        if not clear_existing:
            all_csv_object_ids.update(existing_object_ids)
        
        # Также добавляем object_id из Diagnostics (включая автocозданные)
        if auto_created_objects > 0:
            unique_diag_object_ids = diagnostics_df["object_id"].dropna().unique()
            for obj_id in unique_diag_object_ids:
                try:
                    all_csv_object_ids.add(int(obj_id))
                except:
                    pass
        
        if all_csv_object_ids:
            db_objects = session.query(Object).filter(Object.object_id.in_(list(all_csv_object_ids))).all()
            # Создаем маппинг object_id (из CSV) -> Object.id (в БД)
            for obj in db_objects:
                object_id_map[obj.object_id] = obj.id
        
        # 3. Импорт Diagnostics (файл уже прочитан выше, если objects_csv_path был None)
        if objects_csv_path is not None:
            diagnostics_df = _read_data_file(diagnostics_csv_path)
        
        # Сохраняем имя исходного файла для отслеживания
        source_file_objects = objects_csv_path.name if objects_csv_path else "AUTO-CREATED"
        source_file_diagnostics = diagnostics_csv_path.name
        
        # Получаем существующие diag_id для проверки дубликатов
        existing_diag_ids = set()
        if not clear_existing:
            existing_diagnostics = session.query(Diagnostic.diag_id).all()
            existing_diag_ids = {row[0] for row in existing_diagnostics}
        
        # Создаем маппинг object_id -> year для использования в ML
        object_year_map = {obj.object_id: obj.year for obj in db_objects if obj.year}
        
        diagnostics = []
        diagnostics_for_ml = []  # Диагностики без ml_label для предсказания
        skipped_diagnostics = 0
        
        for idx, row in diagnostics_df.iterrows():
            try:
                csv_diag_id = int(row["diag_id"])
                
                # Проверяем дубликаты, если не очищаем существующие данные
                if not clear_existing and csv_diag_id in existing_diag_ids:
                    skipped_diagnostics += 1
                    continue  # Пропускаем существующую диагностику
                
                csv_object_id = int(row["object_id"])
                db_object_id = object_id_map.get(csv_object_id)
                
                if not db_object_id:
                    errors.append(f"Диагностика строка {idx + 2}: object_id {csv_object_id} не найден")
                    continue
                
                method_str = str(row["method"]).upper()
                # Поддерживаем все методы из ТЗ
                valid_methods = ["VIK", "PVK", "MPK", "UZK", "RGK", "TVK", "VIBRO", "MFL", "TFI", "GEO", "UTWM", "UT", "EC"]
                if method_str not in valid_methods:
                    errors.append(f"Диагностика строка {idx + 2}: неверный method '{row['method']}'. Допустимые: {', '.join(valid_methods)}")
                    continue
                
                date = pd.to_datetime(row["date"]).date()
                
                # ВСЕГДА анализируем диагностику для определения критичности на основе реальных данных
                # Добавляем в список для анализа (ML или правило-основанная логика)
                diagnostics_for_ml.append({
                    "index": idx,
                    "row": row,
                    "db_object_id": db_object_id,
                    "method": method_str,
                    "date": date,
                    "object_year": object_year_map.get(csv_object_id),
                })
                
                # Парсим quality_grade
                quality_grade = None
                if pd.notna(row.get("quality_grade")) and str(row["quality_grade"]).strip():
                    quality_grade_str = str(row["quality_grade"]).strip().lower()
                    quality_grade_map = {
                        "удовлетворительно": QualityGrade.УДОВЛЕТВОРИТЕЛЬНО,
                        "допустимо": QualityGrade.ДОПУСТИМО,
                        "требует_мер": QualityGrade.ТРЕБУЕТ_МЕР,
                        "недопустимо": QualityGrade.НЕДОПУСТИМО,
                    }
                    if quality_grade_str in quality_grade_map:
                        quality_grade = quality_grade_map[quality_grade_str]
                
                diag = Diagnostic(
                    diag_id=csv_diag_id,
                    object_id=db_object_id,  # Используем ID из БД
                    method=DiagnosticMethod(method_str),
                    date=date,
                    temperature=float(row["temperature"]) if pd.notna(row.get("temperature")) else None,
                    humidity=float(row["humidity"]) if pd.notna(row.get("humidity")) else None,
                    illumination=float(row["illumination"]) if pd.notna(row.get("illumination")) else None,
                    defect_found=bool(row.get("defect_found", False)),
                    defect_description=str(row["defect_description"]) if pd.notna(row.get("defect_description")) else None,
                    quality_grade=quality_grade,
                    param1=float(row["param1"]) if pd.notna(row.get("param1")) else None,
                    param2=float(row["param2"]) if pd.notna(row.get("param2")) else None,
                    param3=float(row["param3"]) if pd.notna(row.get("param3")) else None,
                    ml_label=None,  # Будет установлено после анализа критичности
                    source_file=source_file_diagnostics,  # Сохраняем имя исходного файла
                )
                diagnostics.append(diag)
            except Exception as e:
                errors.append(f"Диагностика строка {idx + 2}: {str(e)}")
        
        # Анализ критичности для ВСЕХ диагностик
        ml_predictions = {}
        if diagnostics_for_ml:
            try:
                logger.info(f"Анализирую критичность для {len(diagnostics_for_ml)} диагностик...")
                
                # Подготавливаем данные для анализа
                ml_data = []
                for diag_info in diagnostics_for_ml:
                    row = diag_info["row"]
                    ml_data.append({
                        "method": diag_info["method"],
                        "param1": float(row["param1"]) if pd.notna(row.get("param1")) else 0.0,
                        "param2": float(row["param2"]) if pd.notna(row.get("param2")) else 0.0,
                        "param3": float(row["param3"]) if pd.notna(row.get("param3")) else 0.0,
                        "defect_found": bool(row.get("defect_found", False)),
                        "defect_description": str(row.get("defect_description", "")).lower() if pd.notna(row.get("defect_description")) else "",
                        "object_year": diag_info["object_year"] or 2000,
                    })
                
                # Используем ML модель, если она обучена
                if ml_model.is_trained:
                    logger.info("Использую обученную ML модель для анализа критичности")
                    ml_df = pd.DataFrame(ml_data)
                    features = ml_model.prepare_features(ml_df)
                    predictions = ml_model.predict(features)
                    
                    # Сохраняем предсказания
                    for i, diag_info in enumerate(diagnostics_for_ml):
                        pred_label = predictions[i]
                        if pred_label in ["normal", "medium", "high"]:
                            ml_predictions[diag_info["index"]] = MLLabel(pred_label)
                else:
                    # Используем правило-основанную логику, если модель не обучена
                    logger.info("ML модель не обучена, использую правило-основанную логику")
                    for i, diag_info in enumerate(diagnostics_for_ml):
                        data = ml_data[i]
                        criticality = _determine_criticality_by_rules(
                            defect_found=data["defect_found"],
                            defect_description=data["defect_description"],
                            param1=data["param1"],
                            param2=data["param2"],
                            param3=data["param3"],
                            method=data["method"],
                        )
                        ml_predictions[diag_info["index"]] = MLLabel(criticality)
                
                logger.info(f"Анализ критичности завершен: {len(ml_predictions)} меток определено")
            except Exception as e:
                logger.error(f"Ошибка при анализе критичности: {e}", exc_info=True)
                errors.append(f"Ошибка анализа критичности: {str(e)}")
        
        # Обновляем ml_label для диагностик с предсказаниями
        # Создаем маппинг diag_id -> ml_label для быстрого поиска
        diag_id_to_ml_label = {}
        for diag_info in diagnostics_for_ml:
            if diag_info["index"] in ml_predictions:
                diag_id = int(diagnostics_df.iloc[diag_info["index"]]["diag_id"])
                diag_id_to_ml_label[diag_id] = ml_predictions[diag_info["index"]]
        
        # Применяем предсказания к диагностикам (перезаписываем даже если была метка в CSV)
        for diag in diagnostics:
            if diag.diag_id in diag_id_to_ml_label:
                diag.ml_label = diag_id_to_ml_label[diag.diag_id]
                logger.debug(f"Установлена критичность {diag.ml_label.value} для диагностики {diag.diag_id}")
        
        if diagnostics:
            logger.info(f"Импорт {len(diagnostics)} диагностик...")
            session.add_all(diagnostics)
            logger.info(f"Импортировано {len(diagnostics)} диагностик, из них {len(ml_predictions)} с ML предсказаниями")
        
        # Коммитим всю транзакцию одним разом
        logger.info("Коммит транзакции...")
        session.commit()
        logger.info("Импорт завершен успешно")
        
        # Пытаемся обучить ML модель после импорта (если есть достаточно размеченных данных)
        train_result = {"trained": False, "samples": 0}
        if not ml_model.is_trained:
            logger.info("Попытка автоматического обучения ML модели...")
            train_result = _train_model_sync(session)
            if train_result.get("trained"):
                logger.info(f"✅ ML модель автоматически обучена на {train_result.get('samples')} записях")
            else:
                logger.info(f"⚠️  ML модель не обучена: недостаточно данных ({train_result.get('samples', 0)} записей)")
        
        # Периодический мониторинг ML модели через OpenAI (каждый 10-й импорт)
        try:
            from app.services.ml_monitor import monitor_and_improve
            import random
            # Мониторим случайно в 10% случаев или если модель только что обучилась
            if train_result.get("trained") or random.random() < 0.1:
                logger.info("Запуск мониторинга ML модели через OpenAI...")
                monitor_result = monitor_and_improve(session, auto_improve=False)
                if monitor_result.get("ai_analysis"):
                    logger.info("✅ OpenAI анализ ML модели выполнен")
                    # Логируем рекомендации
                    for suggestion in monitor_result.get("suggestions", [])[:3]:  # Первые 3
                        logger.info(f"💡 Рекомендация: {suggestion.get('message', '')}")
        except Exception as e:
            logger.debug(f"Мониторинг ML через OpenAI пропущен: {e}")
        
        return {
            "success": True,
            "pipelines_imported": len(pipeline_map),
            "objects_imported": len(objects),
            "objects_auto_created": auto_created_objects,
            "objects_skipped": skipped_objects,
            "diagnostics_imported": len(diagnostics),
            "diagnostics_skipped": skipped_diagnostics,
            "ml_predictions_made": len(ml_predictions),
            "errors": errors,
        }
    
    except Exception as e:
        logger.error(f"Ошибка при импорте: {e}", exc_info=True)
        session.rollback()
        logger.error("Транзакция откачена")
        return {
            "success": False,
            "error": str(e),
            "errors": errors,
        }
