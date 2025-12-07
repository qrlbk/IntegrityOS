# Архитектура IntegrityOS MVP

## 🎯 Общая концепция

Система построена по принципу монорепозитория с разделением на frontend (Next.js) и backend (FastAPI). Основной фокус — интерактивная карта с визуализацией состояния трубопроводов и ML-анализ дефектов.

## 📐 Архитектурные решения

### 1. Frontend Architecture (Next.js App Router)

```
frontend/
├── app/
│   ├── (dashboard)/
│   │   ├── page.tsx           # Главная страница с картой
│   │   ├── dashboard/
│   │   │   └── page.tsx       # Дашборд со статистикой
│   │   └── reports/
│   │       └── page.tsx       # Генерация PDF
│   ├── api/                    # API routes (proxy к FastAPI)
│   └── layout.tsx
├── components/
│   ├── map/
│   │   ├── PipelineMap.tsx    # Основной компонент карты
│   │   ├── MarkerCluster.tsx   # Кластеризация точек
│   │   └── RiskLegend.tsx      # Легенда рисков
│   ├── dashboard/
│   │   ├── StatsCards.tsx
│   │   └── RiskChart.tsx
│   └── ui/                     # Shadcn компоненты
├── lib/
│   ├── api.ts                  # API клиент
│   └── types.ts                # TypeScript типы
└── hooks/
    └── useMapData.ts           # Хук для данных карты
```

**Ключевые решения:**
- Leaflet с кастомными маркерами для отображения труб
- Кластеризация при зуме для производительности
- Цветовая индикация: зеленый (normal), желтый (medium), красный (high)
- Фильтры по методам контроля (VIK, MFL, UTWM)

### 2. Backend Architecture (FastAPI)

```
backend/
├── app/
│   ├── main.py                 # Точка входа
│   ├── api/
│   │   ├── v1/
│   │   │   ├── objects.py      # CRUD для объектов
│   │   │   ├── diagnostics.py # CRUD для диагностики
│   │   │   ├── import.py       # Импорт CSV
│   │   │   └── ml.py           # ML endpoints
│   ├── core/
│   │   ├── config.py           # Конфигурация
│   │   ├── database.py         # DB connection
│   │   └── ml_model.py         # ML модель
│   ├── models/
│   │   ├── object.py
│   │   └── diagnostic.py
│   ├── schemas/
│   │   ├── object.py
│   │   └── diagnostic.py
│   └── services/
│       ├── import_service.py   # Логика импорта CSV
│       ├── ml_service.py       # ML логика
│       └── report_service.py   # Генерация PDF
├── alembic/                    # Миграции БД
└── tests/
```

**Ключевые решения:**
- RESTful API с версионированием (v1)
- Валидация через Pydantic
- Асинхронные операции для импорта больших CSV
- ML-модель загружается при старте (Singleton pattern)

### 3. ML Pipeline

**Подход:** Гибридный (pretrained + fine-tuning)

1. **Базовая модель:** Обучена на исторических данных (если есть)
2. **Online Learning:** При импорте новых размеченных данных — дообучение
3. **Inference:** При импорте данных без `ml_label` — предсказание

**Модель:**
- Алгоритм: Random Forest или Gradient Boosting (XGBoost)
- Features: `param1`, `param2`, `method`, `defect_found`, `year` (объекта)
- Target: `ml_label` (normal, medium, high)

**Workflow:**
```
CSV Import → Validation → Feature Extraction → 
  → ML Prediction (if ml_label empty) → 
  → Save to DB → Return results
```

### 4. Database Schema

```sql
-- Objects (оборудование)
CREATE TABLE objects (
    object_id SERIAL PRIMARY KEY,
    object_name VARCHAR(255) NOT NULL,
    object_type VARCHAR(50) CHECK (object_type IN ('crane', 'compressor', 'pipeline_section')),
    pipeline_id VARCHAR(10) NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,
    lon DECIMAL(11, 8) NOT NULL,
    year INTEGER,
    material VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Diagnostics (проверки)
CREATE TABLE diagnostics (
    diag_id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES objects(object_id),
    method VARCHAR(10) CHECK (method IN ('VIK', 'MFL', 'UTWM', 'UT', 'EC')),
    date DATE NOT NULL,
    defect_found BOOLEAN DEFAULT FALSE,
    defect_description TEXT,
    param1 DECIMAL(10, 4),
    param2 DECIMAL(10, 4),
    ml_label VARCHAR(10) CHECK (ml_label IN ('normal', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX idx_objects_pipeline ON objects(pipeline_id);
CREATE INDEX idx_objects_location ON objects(lat, lon);
CREATE INDEX idx_diagnostics_object ON diagnostics(object_id);
CREATE INDEX idx_diagnostics_method ON diagnostics(method);
CREATE INDEX idx_diagnostics_label ON diagnostics(ml_label);
```

## 🔄 Data Flow

### Импорт CSV

```
1. Frontend: Загрузка файла → POST /api/v1/import/csv
2. Backend: 
   - Парсинг CSV (pandas)
   - Валидация схемы (Pydantic)
   - Batch insert в БД
   - ML prediction для записей без ml_label
   - Возврат статистики импорта
3. Frontend: Обновление карты и дашборда
```

### Отображение на карте

```
1. Frontend: GET /api/v1/objects?pipeline_id=MT-01&method=VIK
2. Backend: 
   - Фильтрация по параметрам
   - JOIN с diagnostics для получения ml_label
   - Агрегация рисков по объектам
3. Frontend: 
   - Рендеринг маркеров на Leaflet
   - Кластеризация при зуме
   - Цветовая индикация
```

## 🎨 UI/UX Decisions

1. **Карта — главный элемент:**
   - Полноэкранный режим по умолчанию
   - Боковая панель с фильтрами (collapsible)
   - Popup при клике на маркер: детали объекта + последняя диагностика

2. **Дашборд:**
   - Карточки с метриками (общее количество, критичные, средние)
   - Графики распределения по методам контроля
   - Таблица последних диагностик

3. **Импорт:**
   - Drag & Drop для CSV файлов
   - Прогресс-бар при импорте
   - Валидация с показом ошибок

## 🚀 План реализации MVP (2-3 дня)

### День 1: Backend Foundation
- [x] Структура проекта
- [ ] FastAPI setup + DB models
- [ ] CSV import endpoint
- [ ] Базовый ML-модуль
- [ ] Генератор тестовых данных ✅

### День 2: Frontend + Integration
- [ ] Next.js setup + Shadcn/ui
- [ ] Leaflet карта с базовыми маркерами
- [ ] API integration
- [ ] Фильтры и кластеризация

### День 3: Polish + Features
- [ ] Дашборд со статистикой
- [ ] PDF генерация
- [ ] Оптимизация производительности
- [ ] Тестирование и багфиксы

## 🔧 Технические детали

### ML Model Training

```python
# Псевдокод
features = ['param1', 'param2', 'method_encoded', 'defect_found', 'object_year']
target = 'ml_label'

# Если есть размеченные данные → обучение
if labeled_data_count > 100:
    model.fit(X_train, y_train)
    
# Предсказание для новых данных
predictions = model.predict(X_new)
```

### Performance Optimizations

1. **Карта:**
   - Кластеризация при zoom < 10
   - Lazy loading маркеров
   - Debounce для фильтров

2. **Backend:**
   - Batch inserts (1000 записей за раз)
   - Кэширование ML predictions
   - Асинхронные задачи для больших импортов

3. **Database:**
   - Индексы на часто используемых полях
   - Materialized views для агрегаций (опционально)

## 📝 Next Steps

После MVP можно добавить:
- Real-time обновления (WebSockets)
- Исторические графики деградации
- Интеграция с IoT датчиками
- Мобильное приложение
- Расширенная аналитика

