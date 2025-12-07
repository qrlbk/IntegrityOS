"""
Настройка подключения к базе данных SQLite.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

from app.core.config import settings

# Создаем директорию для БД если её нет
db_dir = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent
if db_dir and not db_dir.exists():
    db_dir.mkdir(parents=True, exist_ok=True)

# Создаем sync engine для SQLite
# echo можно управлять через переменную окружения SQL_ECHO
sql_echo = os.getenv("SQL_ECHO", "false").lower() == "true"
engine = create_engine(
    settings.DATABASE_URL,
    echo=sql_echo,  # Логирование SQL запросов (управляется через SQL_ECHO env var)
    connect_args={"check_same_thread": False},  # Нужно для SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class для моделей
Base = declarative_base()


def get_db():
    """Dependency для получения DB сессии."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
