"""
API endpoints для импорта CSV файлов из локальной папки data/.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
import shutil
import pandas as pd

from app.core.database import get_db
from app.services.import_service import import_data_from_csv

router = APIRouter()


@router.post("/import")
def import_csv_files(
    session: Session = Depends(get_db),
    clear_existing: bool = False,
):
    """
    Импорт данных из CSV/XLSX файлов в папке data/.
    
    Поддерживает форматы:
    - CSV: Objects.csv, Diagnostics.csv
    - XLSX: Objects.xlsx, Diagnostics.xlsx
    
    Автоматически определяет формат по расширению файла.
    
    Args:
        clear_existing: Если True, очищает старые данные перед импортом. 
                       По умолчанию False - данные добавляются к существующим.
    """
    # Определяем пути к файлам (корень проекта)
    # От backend/app/api/v1/import_csv.py -> integrityos/
    project_root = Path(__file__).parent.parent.parent.parent.parent
    data_dir = project_root / "data"
    
    # Ищем файлы объектов (CSV или XLSX)
    objects_path = None
    for ext in [".csv", ".xlsx", ".xls"]:
        path = data_dir / f"Objects{ext}"
        if path.exists():
            objects_path = path
            break
    
    if not objects_path:
        raise HTTPException(
            status_code=404,
            detail=f"Файл Objects.csv/xlsx не найден в {data_dir}"
        )
    
    # Ищем файлы диагностики (CSV или XLSX)
    diagnostics_path = None
    for ext in [".csv", ".xlsx", ".xls"]:
        path = data_dir / f"Diagnostics{ext}"
        if path.exists():
            diagnostics_path = path
            break
    
    if not diagnostics_path:
        raise HTTPException(
            status_code=404,
            detail=f"Файл Diagnostics.csv/xlsx не найден в {data_dir}"
        )
    
    # Импортируем данные
    result = import_data_from_csv(
        session=session,
        objects_csv_path=objects_path,
        diagnostics_csv_path=diagnostics_path,
        clear_existing=clear_existing,  # По умолчанию не очищаем старые данные
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Ошибка импорта"),
        )
    
    return result


def _detect_file_type(df) -> str:
    """
    Определяет тип файла по содержимому (колонкам).
    
    Args:
        df: DataFrame с данными
        
    Returns:
        "objects" или "diagnostics"
    """
    columns_lower = [str(col).lower() for col in df.columns]
    
    # Ключевые колонки для Objects
    objects_keywords = ["object_id", "object_name", "object_type", "lat", "lon", "pipeline_id"]
    objects_score = sum(1 for keyword in objects_keywords if any(keyword in col for col in columns_lower))
    
    # Ключевые колонки для Diagnostics
    diagnostics_keywords = ["diag_id", "method", "defect_found", "defect_description", "param1", "param2"]
    diagnostics_score = sum(1 for keyword in diagnostics_keywords if any(keyword in col for col in columns_lower))
    
    # Определяем тип по наибольшему количеству совпадений
    if objects_score >= 3 and objects_score > diagnostics_score:
        return "objects"
    elif diagnostics_score >= 3:
        return "diagnostics"
    else:
        # Если не удалось определить однозначно, используем дополнительные признаки
        if any("lat" in col or "lon" in col for col in columns_lower):
            return "objects"
        elif any("diag" in col or "method" in col for col in columns_lower):
            return "diagnostics"
        else:
            # По умолчанию считаем, что первый файл - objects, второй - diagnostics
            # Но лучше выбросить ошибку
            raise ValueError("Не удалось определить тип файла. Убедитесь, что файлы содержат правильные колонки.")


@router.post("/import/upload")
async def upload_and_import_files(
    file1: UploadFile = File(None, description="Первый файл (CSV или XLSX) - Objects или Diagnostics"),
    file2: UploadFile = File(None, description="Второй файл (CSV или XLSX) - Objects или Diagnostics (опционально)"),
    clear_existing: bool = Query(False, description="Очистить существующие данные перед импортом"),
    session: Session = Depends(get_db),
):
    """
    Загрузка и импорт файлов через веб-интерфейс.
    
    Может принимать один или два файла:
    - Если загружен только Diagnostics: система автоматически создаст объекты (AI/ML анализ)
    - Если загружены оба файла: стандартный импорт Objects + Diagnostics
    
    Система автоматически определяет тип файла по содержимому (колонкам):
    - Файл с колонками object_id, object_name, lat, lon - это Objects
    - Файл с колонками diag_id, method, defect_found - это Diagnostics
    
    Поддерживаемые форматы: CSV, XLSX, XLS
    
    Args:
        file1: Первый файл (обязательно)
        file2: Второй файл (опционально - если не указан, будет импорт только Diagnostics)
        clear_existing: Если True, очищает старые данные перед импортом.
                       По умолчанию False - данные добавляются к существующим.
    """
    import pandas as pd
    
    # Проверяем, что хотя бы один файл загружен
    if file1 is None or file1.filename is None:
        raise HTTPException(
            status_code=400,
            detail="Необходимо загрузить хотя бы один файл (Diagnostics или оба файла)"
        )
    
    # Валидация расширений файлов
    valid_extensions = ['.csv', '.xlsx', '.xls']
    
    file1_ext = Path(file1.filename).suffix.lower()
    
    if file1_ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный формат первого файла: {file1_ext}. Поддерживаются: {', '.join(valid_extensions)}"
        )
    
    # Если загружен только один файл, проверяем что это Diagnostics
    if file2 is None or file2.filename is None:
        # Импорт только Diagnostics - объекты будут созданы автоматически
        logger.info("Загружен только один файл. Проверяю что это Diagnostics...")
        
        temp_dir = Path(tempfile.mkdtemp())
        file1_path = temp_dir / f"file1{file1_ext}"
        
        try:
            # Сохраняем файл
            with open(file1_path, "wb") as buffer:
                shutil.copyfileobj(file1.file, buffer)
            
            # Определяем тип файла
            if file1_ext == '.xlsx' or file1_ext == '.xls':
                df1 = pd.read_excel(file1_path, nrows=5)
            else:
                df1 = pd.read_csv(file1_path, nrows=5)
            
            type1 = _detect_file_type(df1)
            
            if type1 != "diagnostics":
                raise HTTPException(
                    status_code=400,
                    detail=f"Если загружен только один файл, это должен быть Diagnostics. Обнаружен тип: {type1}"
                )
            
            # Импортируем только Diagnostics (объекты создадутся автоматически)
            result = import_data_from_csv(
                session=session,
                diagnostics_csv_path=file1_path,
                objects_csv_path=None,  # None - объекты создадутся автоматически
                clear_existing=clear_existing,
            )
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=500,
                    detail=result.get("error", "Ошибка импорта"),
                )
            
            return result
        
        finally:
            try:
                if file1_path.exists():
                    file1_path.unlink()
                if temp_dir.exists():
                    temp_dir.rmdir()
            except Exception:
                pass
    
    # Если оба файла загружены - стандартная логика
    file2_ext = Path(file2.filename).suffix.lower()
    
    if file2_ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный формат второго файла: {file2_ext}. Поддерживаются: {', '.join(valid_extensions)}"
        )
    
    # Сохраняем файлы во временную директорию
    temp_dir = Path(tempfile.mkdtemp())
    file1_path = temp_dir / f"file1{file1_ext}"
    file2_path = temp_dir / f"file2{file2_ext}"
    
    try:
        # Сохраняем загруженные файлы
        with open(file1_path, "wb") as buffer:
            shutil.copyfileobj(file1.file, buffer)
        
        with open(file2_path, "wb") as buffer:
            shutil.copyfileobj(file2.file, buffer)
        
        # Определяем тип каждого файла по содержимому
        # Читаем оба файла для определения типа
        if file1_ext == '.xlsx' or file1_ext == '.xls':
            df1 = pd.read_excel(file1_path, nrows=5)  # Читаем только первые строки для определения
        else:
            df1 = pd.read_csv(file1_path, nrows=5)
        
        if file2_ext == '.xlsx' or file2_ext == '.xls':
            df2 = pd.read_excel(file2_path, nrows=5)
        else:
            df2 = pd.read_csv(file2_path, nrows=5)
        
        # Определяем тип каждого файла
        type1 = _detect_file_type(df1)
        type2 = _detect_file_type(df2)
        
        # Проверяем, что файлы разных типов
        if type1 == type2:
            raise HTTPException(
                status_code=400,
                detail=f"Оба файла имеют одинаковый тип ({type1}). Нужны файлы разных типов: один с объектами, другой с диагностиками."
            )
        
        # Определяем, какой файл - Objects, а какой - Diagnostics
        if type1 == "objects":
            objects_path = file1_path
            diagnostics_path = file2_path
        else:
            objects_path = file2_path
            diagnostics_path = file1_path
        
        # Импортируем данные
        result = import_data_from_csv(
            session=session,
            objects_csv_path=objects_path,
            diagnostics_csv_path=diagnostics_path,
            clear_existing=clear_existing,  # По умолчанию не очищаем старые данные
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Ошибка импорта"),
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке файлов: {str(e)}"
        )
    finally:
        # Удаляем временные файлы
        try:
            if file1_path.exists():
                file1_path.unlink()
            if file2_path.exists():
                file2_path.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()
        except Exception:
            pass  # Игнорируем ошибки при удалении временных файлов


@router.get("/import/hackathon/objects")
def get_hackathon_objects_file():
    """
    Возвращает файл Objects_hackathon.csv для загрузки тестовых данных.
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    hackathon_file = project_root / "data" / "Objects_hackathon.csv"
    
    if not hackathon_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Файл Objects_hackathon.csv не найден. Запустите convert_hackathon_data.py для его создания."
        )
    
    return FileResponse(
        path=hackathon_file,
        filename="Objects_hackathon.csv",
        media_type="text/csv"
    )


@router.get("/import/hackathon/diagnostics")
def get_hackathon_diagnostics_file():
    """
    Возвращает файл Diagnostics_hackathon.csv для загрузки тестовых данных.
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    hackathon_file = project_root / "data" / "Diagnostics_hackathon.csv"
    
    if not hackathon_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Файл Diagnostics_hackathon.csv не найден. Запустите convert_hackathon_data.py для его создания."
        )
    
    return FileResponse(
        path=hackathon_file,
        filename="Diagnostics_hackathon.csv",
        media_type="text/csv"
    )


@router.get("/import/template/objects")
def get_objects_template():
    """
    Возвращает шаблон CSV файла для объектов.
    Содержит примеры заполнения и правильную структуру колонок.
    """
    from app.services.template_service import generate_objects_template
    from fastapi.responses import Response
    
    csv_data, filename = generate_objects_template()
    
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@router.get("/import/template/diagnostics")
def get_diagnostics_template():
    """
    Возвращает шаблон CSV файла для диагностики.
    Содержит примеры заполнения, структурированные для лучшего понимания ML и AI.
    """
    from app.services.template_service import generate_diagnostics_template
    from fastapi.responses import Response
    
    csv_data, filename = generate_diagnostics_template()
    
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@router.get("/import/template/both")
def get_both_templates():
    """
    Возвращает ZIP архив с обоими шаблонами.
    """
    from app.services.template_service import generate_objects_template, generate_diagnostics_template
    from fastapi.responses import Response
    import zipfile
    import io
    
    # Генерируем оба шаблона
    objects_data, objects_name = generate_objects_template()
    diagnostics_data, diagnostics_name = generate_diagnostics_template()
    
    # Создаем ZIP архив в памяти
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(objects_name, objects_data)
        zip_file.writestr(diagnostics_name, diagnostics_data)
        # Добавляем README с инструкциями
        readme_path = Path(__file__).parent.parent.parent / "services" / "template_instructions.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
        else:
            # Fallback, если файл не найден
            readme_content = """# ШАБЛОНЫ ОТЧЕТОВ ДЛЯ СИСТЕМЫ IntegrityOS

## Файлы в архиве:
1. Objects_template.csv - Шаблон для объектов (оборудование)
2. Diagnostics_template.csv - Шаблон для диагностики

## Инструкция по заполнению:

### Objects_template.csv
- object_id: Уникальный ID объекта (целое число)
- object_name: Название объекта
- object_type: crane, compressor или pipeline_section
- pipeline_id: ID трубопровода (MT-01, MT-02 и т.д.)
- lat, lon: Координаты объекта
- year, material: Опционально

### Diagnostics_template.csv
ВАЖНО для ML и AI анализа:

1. defect_description - ОПИСЫВАЙТЕ ДЕТАЛЬНО:
   ✅ ХОРОШО: "Глубокая коррозия 25мм на участке 10-15 метров. Требуется немедленный ремонт."
   ❌ ПЛОХО: "Дефект"

2. Заполняйте параметры (param1, param2, param3):
   - param1: Глубина/толщина (мм)
   - param2: Площадь/ширина (см²/мм)
   - param3: Длина/доп. параметр (м)

3. Используйте ключевые слова в описании для лучшего анализа AI:
   - Высокий риск: "критический", "аварийный", "сквозная", "разрушение"
   - Средний риск: "глубокая коррозия", "трещина", "требуется ремонт"
   - Низкий риск: "поверхностная", "мониторинг", "удовлетворительно"

4. ml_label можно оставить пустым - система определит автоматически на основе описания и параметров.

## После заполнения:
Загрузите оба файла на странице "Новый импорт" в системе.
"""
        zip_file.writestr("README.txt", readme_content.encode('utf-8'))
    
    zip_buffer.seek(0)
    
    return Response(
        content=zip_buffer.read(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="IntegrityOS_Report_Templates.zip"',
        }
    )


@router.post("/import/hackathon")
def import_hackathon_data(
    session: Session = Depends(get_db),
    clear_existing: bool = False,
):
    """
    Импорт тестовых данных хакатона из файлов Objects_hackathon.csv и Diagnostics_hackathon.csv.
    
    Args:
        clear_existing: Если True, очищает старые данные перед импортом.
                       По умолчанию False - данные добавляются к существующим.
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    data_dir = project_root / "data"
    
    objects_path = data_dir / "Objects_hackathon.csv"
    diagnostics_path = data_dir / "Diagnostics_hackathon.csv"
    
    if not objects_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Файл Objects_hackathon.csv не найден в {data_dir}. Запустите convert_hackathon_data.py для его создания."
        )
    
    if not diagnostics_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Файл Diagnostics_hackathon.csv не найден в {data_dir}. Запустите convert_hackathon_data.py для его создания."
        )
    
    # Импортируем данные
    result = import_data_from_csv(
        session=session,
        objects_csv_path=objects_path,
        diagnostics_csv_path=diagnostics_path,
        clear_existing=clear_existing,  # По умолчанию не очищаем старые данные
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Ошибка импорта"),
        )
    
    return result
