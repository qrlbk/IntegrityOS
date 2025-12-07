"""add_location_status_and_make_coords_nullable

Revision ID: 62a9378d6bdc
Revises: 07f653db304c
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '62a9378d6bdc'
down_revision = '07f653db304c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite не поддерживает ALTER COLUMN напрямую, используем обходной путь
    # 1. Создаем новую таблицу с нужной структурой
    # 2. Копируем данные
    # 3. Удаляем старую таблицу
    # 4. Переименовываем новую
    
    # Для SQLite используем более простой подход - создаем новую колонку и обновляем данные
    # Затем делаем lat и lon nullable через пересоздание таблицы
    
    # Добавляем новую колонку location_status
    # SQLite не поддерживает ENUM напрямую, используем VARCHAR
    op.add_column('objects', sa.Column('location_status', sa.String(20), nullable=False, server_default='pending'))
    
    # Обновляем существующие объекты: если координаты есть, статус = verified
    # SQLite синтаксис для UPDATE
    op.execute("""
        UPDATE objects 
        SET location_status = 'verified' 
        WHERE lat IS NOT NULL AND lon IS NOT NULL AND lat != 0 AND lon != 0
    """)
    
    # Для изменения nullable в SQLite нужно пересоздать таблицу
    # Но это сложно, поэтому просто обновим существующие NULL значения
    # В SQLite можно вставить NULL даже если колонка NOT NULL была создана с DEFAULT
    # Поэтому просто обновим структуру через пересоздание таблицы
    
    # Создаем временную таблицу с правильной структурой
    op.execute("""
        CREATE TABLE objects_new (
            id INTEGER NOT NULL PRIMARY KEY,
            object_id INTEGER NOT NULL UNIQUE,
            object_name VARCHAR(255) NOT NULL,
            object_type VARCHAR(20) NOT NULL,
            pipeline_id INTEGER NOT NULL,
            lat FLOAT,
            lon FLOAT,
            location_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            year INTEGER,
            material VARCHAR(100),
            created_at DATETIME,
            FOREIGN KEY(pipeline_id) REFERENCES pipelines(id)
        )
    """)
    
    # Копируем данные
    op.execute("""
        INSERT INTO objects_new 
        (id, object_id, object_name, object_type, pipeline_id, lat, lon, location_status, year, material, created_at)
        SELECT 
            id, object_id, object_name, object_type, pipeline_id, 
            CASE WHEN lat = 0 THEN NULL ELSE lat END,
            CASE WHEN lon = 0 THEN NULL ELSE lon END,
            location_status, year, material, created_at
        FROM objects
    """)
    
    # Удаляем старую таблицу
    op.drop_table('objects')
    
    # Переименовываем новую таблицу
    op.rename_table('objects_new', 'objects')
    
    # Создаем индексы
    op.create_index('ix_objects_object_id', 'objects', ['object_id'])
    op.create_index('ix_objects_pipeline_id', 'objects', ['pipeline_id'])
    op.create_index('ix_objects_location_status', 'objects', ['location_status'])


def downgrade() -> None:
    # Откат изменений
    # Создаем таблицу со старой структурой
    op.execute("""
        CREATE TABLE objects_old (
            id INTEGER NOT NULL PRIMARY KEY,
            object_id INTEGER NOT NULL UNIQUE,
            object_name VARCHAR(255) NOT NULL,
            object_type VARCHAR(20) NOT NULL,
            pipeline_id INTEGER NOT NULL,
            lat FLOAT NOT NULL,
            lon FLOAT NOT NULL,
            year INTEGER,
            material VARCHAR(100),
            created_at DATETIME,
            FOREIGN KEY(pipeline_id) REFERENCES pipelines(id)
        )
    """)
    
    # Копируем данные, заменяя NULL на 0
    op.execute("""
        INSERT INTO objects_old 
        (id, object_id, object_name, object_type, pipeline_id, lat, lon, year, material, created_at)
        SELECT 
            id, object_id, object_name, object_type, pipeline_id,
            COALESCE(lat, 0.0),
            COALESCE(lon, 0.0),
            year, material, created_at
        FROM objects
    """)
    
    # Удаляем новую таблицу
    op.drop_table('objects')
    
    # Переименовываем старую таблицу
    op.rename_table('objects_old', 'objects')
    
    # Создаем индексы
    op.create_index('ix_objects_object_id', 'objects', ['object_id'])
    op.create_index('ix_objects_pipeline_id', 'objects', ['pipeline_id'])
