"""
Инициализация базы данных - создание таблиц.
"""
from app.core.database import Base, engine
from app.models import Pipeline, Object, Diagnostic  # Импорт для регистрации моделей


def init_db():
    """Создает все таблицы в базе данных."""
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы успешно!")


if __name__ == "__main__":
    init_db()


