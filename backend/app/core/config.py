"""
Конфигурация приложения.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Database (SQLite)
    DATABASE_URL: str = "sqlite:///./integrity.db"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    # ML Model
    ML_MODEL_PATH: str = "app/models/ml_model.pkl"
    ML_MIN_SAMPLES_FOR_TRAINING: int = 100
    ML_TEST_SIZE: float = 0.2  # Размер тестовой выборки
    ML_RANDOM_STATE: int = 42  # Для воспроизводимости
    
    # MLflow
    MLFLOW_TRACKING_URI: str = "file:./mlruns"  # Локальное хранилище
    MLFLOW_EXPERIMENT_NAME: str = "integrityos-pipeline"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PREDICTION_CACHE_TTL: int = 3600  # TTL для кэша предсказаний (1 час)
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # OpenAI (опционально, для AI Assistant)
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
