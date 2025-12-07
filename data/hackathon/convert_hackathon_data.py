#!/usr/bin/env python3
"""
Конвертер данных хакатона в формат IntegrityOS.

Преобразует processed_data.csv в формат Objects.csv и Diagnostics.csv.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Пути к файлам
HACKATHON_DIR = Path(__file__).parent
INPUT_CSV = HACKATHON_DIR / "csv" / "processed_data.csv"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data"
OUTPUT_OBJECTS = OUTPUT_DIR / "Objects_hackathon.csv"
OUTPUT_DIAGNOSTICS = OUTPUT_DIR / "Diagnostics_hackathon.csv"


def convert_hackathon_data():
    """Конвертирует данные хакатона в формат IntegrityOS."""
    print("=" * 80)
    print("КОНВЕРТАЦИЯ ДАННЫХ ХАКАТОНА")
    print("=" * 80)
    
    if not INPUT_CSV.exists():
        print(f"❌ Файл не найден: {INPUT_CSV}")
        sys.exit(1)
    
    # Читаем исходный файл
    print(f"\n📖 Чтение файла: {INPUT_CSV}")
    try:
        df = pd.read_csv(INPUT_CSV, sep=';', encoding='windows-1251')
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        sys.exit(1)
    
    print(f"   Найдено строк: {len(df)}")
    print(f"   Столбцов: {len(df.columns)}")
    
    # Определяем маппинг столбцов
    # На основе анализа: координаты в столбцах 20-21 (Unnamed: 20, Unnamed: 21)
    # Метод: "Магнитоскан" (MFL) в столбце 6
    # Дефекты: в столбце 9 (Unnamed: 9)
    # Параметры: столбцы 530, 0-15
    
    lat_col = None
    lon_col = None
    method_col = None
    defect_col = None
    param1_col = None
    param2_col = None
    
    # Ищем столбцы по содержимому
    for col in df.columns:
        col_lower = str(col).lower()
        # Координаты (найдены в анализе: 48.47-48.48, 57.66-57.67)
        if 'unnamed: 20' in col_lower or (df[col].dtype in [np.float64, np.int64] and 
            len(df[col].dropna()) > 0 and 
            40 <= df[col].dropna().min() <= 50 and 
            40 <= df[col].dropna().max() <= 50):
            if lat_col is None:
                lat_col = col
        if 'unnamed: 21' in col_lower or (df[col].dtype in [np.float64, np.int64] and 
            len(df[col].dropna()) > 0 and 
            50 <= df[col].dropna().min() <= 60 and 
            50 <= df[col].dropna().max() <= 60):
            if lon_col is None:
                lon_col = col
    
    # Ищем метод диагностики
    for col in df.columns:
        if 'магнитоскан' in str(col).lower():
            method_col = col
            break
    
    # Ищем описание дефекта
    for col in df.columns:
        if 'unnamed: 9' in str(col).lower():
            defect_col = col
            break
    
    # Ищем параметры (530, 0-15)
    for col in df.columns:
        if str(col) == '530':
            param1_col = col
        elif str(col) == '0-15':
            param2_col = col
    
    print(f"\n🔍 Найденные столбцы:")
    print(f"   - Широта: {lat_col}")
    print(f"   - Долгота: {lon_col}")
    print(f"   - Метод: {method_col}")
    print(f"   - Дефект: {defect_col}")
    print(f"   - Параметр 1: {param1_col}")
    print(f"   - Параметр 2: {param2_col}")
    
    if not lat_col or not lon_col:
        print("❌ Не удалось найти координаты!")
        sys.exit(1)
    
    # Создаем Objects.csv
    print(f"\n📦 Создание Objects.csv...")
    objects = []
    object_id = 1
    
    # Группируем по координатам для создания объектов
    # (одна точка = один объект)
    seen_coords = {}
    
    for idx, row in df.iterrows():
        try:
            lat = float(row[lat_col]) if pd.notna(row[lat_col]) else None
            lon = float(row[lon_col]) if pd.notna(row[lon_col]) else None
            
            if lat is None or lon is None:
                continue
            
            # Округляем координаты для группировки близких точек
            lat_rounded = round(lat, 4)
            lon_rounded = round(lon, 4)
            coord_key = (lat_rounded, lon_rounded)
            
            if coord_key not in seen_coords:
                seen_coords[coord_key] = object_id
                objects.append({
                    "object_id": object_id,
                    "object_name": f"HACK-Section-{object_id:04d}",
                    "object_type": "pipeline_section",
                    "pipeline_id": "HACK-01",  # Генерируем pipeline_id
                    "lat": lat,
                    "lon": lon,
                    "year": None,  # Неизвестно
                    "material": None,  # Неизвестно
                })
                object_id += 1
        except Exception as e:
            print(f"⚠️  Ошибка обработки строки {idx + 2}: {e}")
            continue
    
    objects_df = pd.DataFrame(objects)
    objects_df.to_csv(OUTPUT_OBJECTS, index=False, encoding='utf-8')
    print(f"✅ Создан {OUTPUT_OBJECTS} с {len(objects)} объектами")
    
    # Создаем Diagnostics.csv
    print(f"\n🔍 Создание Diagnostics.csv...")
    diagnostics = []
    diag_id = 1
    
    for idx, row in df.iterrows():
        try:
            lat = float(row[lat_col]) if pd.notna(row[lat_col]) else None
            lon = float(row[lon_col]) if pd.notna(row[lon_col]) else None
            
            if lat is None or lon is None:
                continue
            
            # Находим object_id по координатам
            lat_rounded = round(lat, 4)
            lon_rounded = round(lon, 4)
            coord_key = (lat_rounded, lon_rounded)
            obj_id = seen_coords.get(coord_key)
            
            if obj_id is None:
                continue
            
            # Метод диагностики
            method = "MFL"  # По умолчанию MFL (Магнитоскан)
            if method_col and pd.notna(row[method_col]):
                method = "MFL"
            
            # Дата (из столбца 8 или текущая)
            date_str = None
            for col in df.columns:
                if '01.01.2025' in str(col) or 'date' in str(col).lower():
                    date_str = str(row[col]) if pd.notna(row[col]) else None
                    break
            
            if not date_str:
                date_str = "2025-01-01"  # По умолчанию
            
            # Парсим дату
            try:
                date = pd.to_datetime(date_str, format='%d.%m.%Y').date()
            except:
                date = datetime(2025, 1, 1).date()
            
            # Дефект
            defect_found = False
            defect_description = None
            if defect_col and pd.notna(row[defect_col]):
                defect_text = str(row[defect_col]).strip()
                if defect_text and defect_text.lower() not in ['nan', 'none', '']:
                    defect_found = True
                    defect_description = defect_text
            
            # Параметры
            param1 = None
            param2 = None
            param3 = None
            
            if param1_col and pd.notna(row[param1_col]):
                try:
                    # Заменяем запятую на точку для float
                    param1_val = str(row[param1_col]).replace(',', '.')
                    param1 = float(param1_val)
                except:
                    pass
            
            if param2_col and pd.notna(row[param2_col]):
                try:
                    param2_val = str(row[param2_col]).replace(',', '.')
                    param2 = float(param2_val)
                except:
                    pass
            
            # ML метка (определяем на основе дефекта)
            ml_label = "normal"
            if defect_found:
                if "коррозия" in str(defect_description).lower():
                    if "глубокая" in str(defect_description).lower() or param1 and param1 > 20:
                        ml_label = "high"
                    else:
                        ml_label = "medium"
                else:
                    ml_label = "medium"
            
            # Quality grade
            quality_grade = "удовлетворительно"
            if defect_found:
                if ml_label == "high":
                    quality_grade = "недопустимо"
                elif ml_label == "medium":
                    quality_grade = "требует_мер"
                else:
                    quality_grade = "допустимо"
            
            diagnostics.append({
                "diag_id": diag_id,
                "object_id": obj_id,
                "method": method,
                "date": date.isoformat(),
                "temperature": None,  # Неизвестно
                "humidity": None,  # Неизвестно
                "illumination": None,  # Неизвестно
                "defect_found": str(defect_found),
                "defect_description": defect_description,
                "quality_grade": quality_grade,
                "param1": round(param1, 4) if param1 is not None else "",
                "param2": round(param2, 4) if param2 is not None else "",
                "param3": "",
                "ml_label": ml_label,
            })
            diag_id += 1
            
        except Exception as e:
            print(f"⚠️  Ошибка обработки строки {idx + 2}: {e}")
            continue
    
    diagnostics_df = pd.DataFrame(diagnostics)
    diagnostics_df.to_csv(OUTPUT_DIAGNOSTICS, index=False, encoding='utf-8')
    print(f"✅ Создан {OUTPUT_DIAGNOSTICS} с {len(diagnostics)} диагностиками")
    
    print(f"\n" + "=" * 80)
    print(f"✅ КОНВЕРТАЦИЯ ЗАВЕРШЕНА")
    print(f"=" * 80)
    print(f"\n📋 Результаты:")
    print(f"   - Объектов: {len(objects)}")
    print(f"   - Диагностик: {len(diagnostics)}")
    print(f"\n💡 Следующие шаги:")
    print(f"   1. Проверьте файлы:")
    print(f"      - {OUTPUT_OBJECTS}")
    print(f"      - {OUTPUT_DIAGNOSTICS}")
    print(f"   2. Если все корректно, переименуйте их в Objects.csv и Diagnostics.csv")
    print(f"   3. Импортируйте через API: POST /api/v1/import")


if __name__ == "__main__":
    convert_hackathon_data()


