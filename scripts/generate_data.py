#!/usr/bin/env python3
"""
Генератор реалистичных тестовых данных для IntegrityOS.

Создает CSV файлы с координатами, идущими линией вдоль трассы трубопровода,
а не случайными точками. Данные максимально реалистичны для демонстрации жюри.
"""

import csv
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

# Фиксируем seed для воспроизводимости
random.seed(42)
np.random.seed(42)

# Конфигурация
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# Трассы трубопроводов в Казахстане (реалистичные координаты)
PIPELINE_ROUTES = {
    "MT-01": {
        "start": (47.1, 51.9),   # Западный Казахстан (Атырау)
        "end": (46.5, 52.5),     # Западный Казахстан (Актау)
        "length_km": 450,
        "description": "Западный маршрут"
    },
    "MT-02": {
        "start": (51.1694, 71.4491),  # Астана (Центральный Казахстан)
        "end": (49.9935, 73.1047),    # Караганда
        "length_km": 220,
        "description": "Центральный маршрут"
    },
    "MT-03": {
        "start": (43.2220, 76.8512),  # Алматы (Южный Казахстан)
        "end": (42.3416, 69.5901),   # Шымкент
        "length_km": 700,
        "description": "Южный маршрут"
    },
}

# Типы объектов и их распределение
OBJECT_TYPES = {
    "pipeline_section": 0.80,  # 80%
    "crane": 0.10,             # 10%
    "compressor": 0.10,        # 10%
}

# Методы диагностики
METHODS = ["VIK", "MFL", "UTWM", "UT", "EC"]

# Материалы труб
MATERIALS = ["Steel-X70", "Steel-20", "09G2S", "Steel-X65", "Steel-17G1S"]

# ML метки
ML_LABELS = ["normal", "medium", "high"]

# Типы дефектов для VIK
VIK_DEFECTS = [
    "Коррозия",
    "Коррозия с потерей металла",
    "Трещина",
    "Деформация",
    "Потеря толщины стенки",
    "Сварной шов",
    "Поверхностная коррозия",
    "Глубокая коррозия",
]

# Типы дефектов для других методов
OTHER_DEFECTS = [
    "Трещина",
    "Деформация",
    "Потеря толщины стенки",
    "Сварной шов",
    "Аномалия материала",
]


def generate_coordinates_along_route(
    start: Tuple[float, float],
    end: Tuple[float, float],
    num_points: int,
    jitter: float = 0.02,  # Отклонение в градусах (~2 км)
) -> List[Tuple[float, float, float]]:
    """
    Генерирует координаты точек вдоль маршрута между start и end.
    
    Args:
        start: Начальная точка (lat, lon)
        end: Конечная точка (lat, lon)
        num_points: Количество точек
        jitter: Максимальное отклонение от прямой линии (в градусах)
    
    Returns:
        Список кортежей (lat, lon, distance_km) - расстояние от начала трассы
    """
    lat_start, lon_start = start
    lat_end, lon_end = end
    
    # Вычисляем расстояние для расчета реального расстояния
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Вычисляет расстояние между двумя точками в км."""
        R = 6371  # Радиус Земли в км
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
    
    total_distance = haversine_distance(lat_start, lon_start, lat_end, lon_end)
    
    coordinates = []
    for i in range(num_points):
        # Линейная интерполяция
        t = i / (num_points - 1) if num_points > 1 else 0
        
        # Базовые координаты
        lat = lat_start + (lat_end - lat_start) * t
        lon = lon_start + (lon_end - lon_start) * t
        
        # Перпендикулярное отклонение от прямой линии
        # Вычисляем направление трассы
        dx = lon_end - lon_start
        dy = lat_end - lat_start
        length = np.sqrt(dx**2 + dy**2)
        
        if length > 0:
            # Перпендикулярный вектор
            perp_x = -dy / length
            perp_y = dx / length
            
            # Случайное отклонение
            offset = np.random.normal(0, jitter)
            lat += perp_y * offset
            lon += perp_x * offset
        
        # Расстояние от начала трассы
        distance_km = total_distance * t
        
        coordinates.append((round(lat, 6), round(lon, 6), round(distance_km, 2)))
    
    return coordinates


def generate_objects_csv(num_objects: int = 400) -> None:
    """Генерирует Objects.csv с реалистичными данными."""
    output_file = OUTPUT_DIR / "Objects.csv"
    
    objects = []
    object_id = 1
    
    # Распределяем объекты по трассам пропорционально длине
    total_length = sum(route["length_km"] for route in PIPELINE_ROUTES.values())
    
    for pipeline_id, route in PIPELINE_ROUTES.items():
        # Количество объектов для этой трассы
        num_objects_for_pipeline = int(
            num_objects * route["length_km"] / total_length
        )
        
        # Генерируем координаты вдоль маршрута
        coords = generate_coordinates_along_route(
            route["start"], 
            route["end"], 
            num_objects_for_pipeline,
            jitter=0.015  # Небольшое отклонение для реалистичности
        )
        
        # Распределяем типы объектов
        type_weights = list(OBJECT_TYPES.values())
        type_names = list(OBJECT_TYPES.keys())
        
        for i, (lat, lon, distance) in enumerate(coords):
            # Выбираем тип объекта согласно распределению
            object_type = np.random.choice(type_names, p=type_weights)
            
            # Генерируем имя объекта
            if object_type == "pipeline_section":
                object_name = f"{pipeline_id}-Section-{i+1:04d}"
            elif object_type == "compressor":
                object_name = f"{pipeline_id}-Compressor-{i+1:02d}"
            else:  # crane
                object_name = f"{pipeline_id}-Crane-{i+1:02d}"
            
            # Год постройки (чем дальше от начала, тем новее объекты)
            # Старые объекты в начале трассы, новые в конце
            base_year = 1985
            year_variation = int((distance / route["length_km"]) * 35)  # 35 лет разброса
            year = base_year + year_variation + random.randint(-5, 5)
            year = max(1980, min(2020, year))  # Ограничиваем диапазон
            
            # Материал (зависит от года)
            if year < 1995:
                material = random.choice(["Steel-20", "09G2S", "Steel-17G1S"])
            else:
                material = random.choice(["Steel-X70", "Steel-X65", "Steel-20"])
            
            objects.append({
                "object_id": object_id,
                "object_name": object_name,
                "object_type": object_type,
                "pipeline_id": pipeline_id,
                "lat": lat,
                "lon": lon,
                "year": year,
                "material": material,
            })
            object_id += 1
    
    # Сортируем по object_id
    objects.sort(key=lambda x: x["object_id"])
    
    # Записываем в CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "object_id",
                "object_name",
                "object_type",
                "pipeline_id",
                "lat",
                "lon",
                "year",
                "material",
            ],
        )
        writer.writeheader()
        writer.writerows(objects)
    
    print(f"✅ Создан {output_file} с {len(objects)} объектами")
    print(f"   Распределение по трассам:")
    for pipeline_id in PIPELINE_ROUTES.keys():
        count = sum(1 for obj in objects if obj["pipeline_id"] == pipeline_id)
        print(f"   - {pipeline_id}: {count} объектов")


def generate_diagnostics_csv(num_diagnostics: int = 1800) -> None:
    """Генерирует Diagnostics.csv с реалистичными данными и логикой дефектов."""
    output_file = OUTPUT_DIR / "Diagnostics.csv"
    
    # Читаем объекты для получения object_id
    objects_file = OUTPUT_DIR / "Objects.csv"
    if not objects_file.exists():
        print("⚠️  Сначала нужно создать Objects.csv")
        generate_objects_csv()
    
    # Загружаем объекты в DataFrame
    df_objects = pd.read_csv(objects_file)
    object_ids = df_objects["object_id"].tolist()
    object_years = dict(zip(df_objects["object_id"], df_objects["year"]))
    object_types = dict(zip(df_objects["object_id"], df_objects["object_type"]))
    
    diagnostics = []
    diag_id = 1
    
    # Генерируем диагностики за период 2023-2025
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range = (end_date - start_date).days
    
    # Распределение методов диагностики (не равномерное)
    method_weights = [0.35, 0.30, 0.15, 0.12, 0.08]  # VIK чаще всего
    
    # Оценки качества согласно ТЗ
    QUALITY_GRADES = ["удовлетворительно", "допустимо", "требует_мер", "недопустимо"]
    
    for _ in range(num_diagnostics):
        object_id = random.choice(object_ids)
        method = np.random.choice(METHODS, p=method_weights)
        
        # Случайная дата в диапазоне
        days_ago = random.randint(0, date_range)
        date = (start_date + timedelta(days=days_ago)).date()
        
        # Генерируем условия окружающей среды (реалистичные для Казахстана)
        # Температура: зависит от сезона (зима: -20 до 0, лето: 15 до 35)
        month = date.month
        if month in [12, 1, 2]:  # Зима
            temperature = random.uniform(-20.0, 5.0)
        elif month in [6, 7, 8]:  # Лето
            temperature = random.uniform(15.0, 35.0)
        else:  # Весна/осень
            temperature = random.uniform(0.0, 20.0)
        
        # Влажность: 30-80% (типично для Казахстана)
        humidity = random.uniform(30.0, 80.0)
        
        # Освещенность: зависит от времени суток и погоды (люкс)
        # Предполагаем дневные измерения: 500-100000 люкс
        illumination = random.uniform(500.0, 100000.0)
        
        # Возраст объекта влияет на вероятность дефекта
        # Целевое распределение: 85% normal, 15% с дефектами
        object_age = datetime.now().year - object_years[object_id]
        base_defect_probability = 0.10  # Базовый 10%
        age_factor = min(0.08, object_age / 200)  # Небольшое влияние возраста
        defect_probability = base_defect_probability + age_factor
        
        # Сначала определяем, есть ли дефект (общая вероятность 15%)
        has_defect = random.random() < defect_probability
        
        # Логика дефектов в зависимости от метода
        defect_found = False
        defect_description = ""
        param1 = None
        param2 = None
        param3 = None
        ml_label = "normal"
        quality_grade = None
        
        if method == "VIK":
            # Визуальный контроль
            if has_defect:
                defect_found = True
                defect_description = random.choice(VIK_DEFECTS)
                
                # Если есть коррозия -> medium или high
                if "коррозия" in defect_description.lower() or "Коррозия" in defect_description:
                    if "глубокая" in defect_description.lower() or "потеря" in defect_description.lower():
                        ml_label = "high"
                    else:
                        ml_label = "medium"
                else:
                    ml_label = random.choice(["normal", "medium"])
                
                # Параметры для VIK (визуальная оценка)
                param1 = random.uniform(0.3, 0.9)  # Оценка серьезности
                param2 = random.uniform(0.2, 0.8)  # Площадь поражения
                param3 = random.uniform(0.1, 0.5)  # Глубина поражения (мм)
            else:
                param1 = random.uniform(0.0, 0.2)
                param2 = random.uniform(0.0, 0.2)
                param3 = random.uniform(0.0, 0.1)
        
        elif method == "MFL":
            # Магнитный поток утечки
            if has_defect:
                # Если есть дефект, генерируем параметры с дефектом
                param1 = random.uniform(20.0, 30.0)  # Глубина в % (дефект)
                param2 = random.uniform(15.0, 50.0)  # Ширина в мм
                param3 = random.uniform(2.0, 5.0)  # Длина дефекта (мм)
                defect_found = True
                defect_description = random.choice(OTHER_DEFECTS)
                if param1 > 25.0:
                    ml_label = "high"
                else:
                    ml_label = "medium"
            else:
                # Нормальные параметры
                param1 = random.uniform(0.0, 18.0)  # Глубина в % (норма)
                param2 = random.uniform(0.0, 15.0)  # Ширина в мм
                param3 = random.uniform(0.0, 1.5)  # Длина (норма)
        
        elif method == "UTWM":
            # Ультразвуковая толщинометрия
            if has_defect:
                # Дефект: потеря толщины
                param1 = random.uniform(5.0, 7.5)  # Толщина стенки в мм (дефект)
                param2 = random.uniform(1.5, 2.5)  # Отклонение от нормы
                param3 = random.uniform(10.0, 30.0)  # Площадь поражения (см²)
                defect_found = True
                defect_description = "Потеря толщины стенки"
                if param1 < 6.0 or param2 > 2.0:
                    ml_label = "high"
                else:
                    ml_label = "medium"
            else:
                # Нормальная толщина
                param1 = random.uniform(8.0, 15.0)  # Толщина стенки в мм (норма)
                param2 = random.uniform(0.0, 1.2)  # Отклонение от нормы
                param3 = random.uniform(0.0, 5.0)  # Площадь (норма)
        
        elif method == "UT":
            # Ультразвуковой контроль
            if has_defect:
                # Дефект обнаружен
                param1 = random.uniform(5.5, 10.0)  # Глубина дефекта в мм
                param2 = random.uniform(15.0, 25.0)  # Длина дефекта в мм
                param3 = random.uniform(3.0, 8.0)  # Ширина дефекта в мм
                defect_found = True
                defect_description = random.choice(OTHER_DEFECTS)
                if param1 > 7.0 or param2 > 20.0:
                    ml_label = "high"
                else:
                    ml_label = "medium"
            else:
                # Нормальные параметры
                param1 = random.uniform(0.0, 4.5)  # Глубина дефекта в мм (норма)
                param2 = random.uniform(0.0, 12.0)  # Длина дефекта в мм
                param3 = random.uniform(0.0, 2.0)  # Ширина (норма)
        
        else:  # EC - вихретоковый контроль
            if has_defect:
                # Дефект обнаружен
                param1 = random.uniform(50.0, 100.0)  # Электропроводность
                param2 = random.uniform(3.5, 5.5)    # Отклонение сигнала (дефект)
                param3 = random.uniform(2.0, 4.0)   # Амплитуда сигнала
                defect_found = True
                defect_description = random.choice(OTHER_DEFECTS)
                if param2 > 4.5:
                    ml_label = "high"
                else:
                    ml_label = "medium"
            else:
                # Нормальные параметры
                param1 = random.uniform(0.0, 100.0)  # Электропроводность
                param2 = random.uniform(0.0, 3.0)    # Отклонение сигнала (норма)
                param3 = random.uniform(0.5, 1.5)   # Амплитуда (норма)
        
        # Определяем quality_grade на основе ml_label и defect_found
        if not defect_found:
            quality_grade = "удовлетворительно"
        elif ml_label == "normal":
            quality_grade = "допустимо"
        elif ml_label == "medium":
            quality_grade = "требует_мер"
        elif ml_label == "high":
            quality_grade = "недопустимо"
        else:
            # Для записей без ml_label
            quality_grade = random.choice(["допустимо", "требует_мер"])
        
        # 20% записей без ml_label (для тестирования ML)
        if random.random() < 0.2:
            ml_label = ""
            # Если нет ml_label, quality_grade может быть неопределенным
            if random.random() < 0.3:
                quality_grade = ""
        
        diagnostics.append({
            "diag_id": diag_id,
            "object_id": object_id,
            "method": method,
            "date": date.isoformat(),
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "illumination": round(illumination, 2),
            "defect_found": str(defect_found),
            "defect_description": defect_description,
            "quality_grade": quality_grade if quality_grade else "",
            "param1": round(param1, 4) if param1 is not None else "",
            "param2": round(param2, 4) if param2 is not None else "",
            "param3": round(param3, 4) if param3 is not None else "",
            "ml_label": ml_label,
        })
        diag_id += 1
    
    # Сортируем по дате
    diagnostics.sort(key=lambda x: x["date"])
    
    # Записываем в CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "diag_id",
                "object_id",
                "method",
                "date",
                "temperature",
                "humidity",
                "illumination",
                "defect_found",
                "defect_description",
                "quality_grade",
                "param1",
                "param2",
                "param3",
                "ml_label",
            ],
        )
        writer.writeheader()
        writer.writerows(diagnostics)
    
    # Статистика
    total = len(diagnostics)
    with_defects = sum(1 for d in diagnostics if d["defect_found"] == "True")
    normal = sum(1 for d in diagnostics if d["ml_label"] == "normal")
    medium = sum(1 for d in diagnostics if d["ml_label"] == "medium")
    high = sum(1 for d in diagnostics if d["ml_label"] == "high")
    no_label = sum(1 for d in diagnostics if d["ml_label"] == "")
    
    print(f"✅ Создан {output_file} с {total} диагностиками")
    print(f"\n📊 Статистика:")
    print(f"   - С дефектами: {with_defects} ({with_defects/total*100:.1f}%)")
    print(f"   - Без дефектов: {total - with_defects} ({(total-with_defects)/total*100:.1f}%)")
    print(f"   - ML метки:")
    print(f"     * normal: {normal} ({normal/total*100:.1f}%)")
    print(f"     * medium: {medium} ({medium/total*100:.1f}%)")
    print(f"     * high: {high} ({high/total*100:.1f}%)")
    print(f"     * без метки: {no_label} ({no_label/total*100:.1f}%)")


def main():
    """Главная функция генерации данных."""
    print("🚀 Генерация реалистичных тестовых данных для IntegrityOS...\n")
    print("=" * 60)
    
    # Генерируем объекты
    print("\n📦 Генерация объектов...")
    generate_objects_csv(num_objects=400)
    
    # Генерируем диагностики
    print("\n🔍 Генерация диагностик...")
    generate_diagnostics_csv(num_diagnostics=1800)
    
    print("\n" + "=" * 60)
    print(f"\n✅ Все файлы созданы в {OUTPUT_DIR}")
    print("\n📋 Итоговая статистика:")
    print(f"   - Трасс: {len(PIPELINE_ROUTES)}")
    print(f"   - Объектов: ~400")
    print(f"   - Диагностик: ~1800")
    print(f"   - Период данных: 2023-2025")
    print("\n💡 Использование:")
    print(f"   - Objects.csv: импорт объектов через API")
    print(f"   - Diagnostics.csv: импорт диагностик через API")
    print(f"   - 20% записей без ml_label для тестирования ML модели")


if __name__ == "__main__":
    main()
