"""
Redis кэш для предсказаний ML модели.
"""
import json
import hashlib
from typing import Optional, Any
import redis
from app.core.config import settings
from app.core.logging_config import logger

try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    # Проверка подключения
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("✅ Redis подключен")
except Exception as e:
    logger.warning(f"⚠️  Redis недоступен: {e}. Кэширование отключено.")
    redis_client = None
    REDIS_AVAILABLE = False


def get_cache_key(features: dict) -> str:
    """Генерирует ключ кэша из признаков."""
    # Создаем хеш из признаков для уникального ключа
    features_str = json.dumps(features, sort_keys=True)
    cache_key = hashlib.md5(features_str.encode()).hexdigest()
    return f"ml_prediction:{cache_key}"


def get_cached_prediction(features: dict) -> Optional[Any]:
    """
    Получить предсказание из кэша.
    
    Args:
        features: Словарь с признаками
        
    Returns:
        Предсказание или None если не найдено
    """
    if not REDIS_AVAILABLE:
        return None
    
    try:
        cache_key = get_cache_key(features)
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Ошибка чтения из Redis: {e}")
    
    return None


def cache_prediction(features: dict, prediction: Any, ttl: int = None) -> bool:
    """
    Сохранить предсказание в кэш.
    
    Args:
        features: Словарь с признаками
        prediction: Предсказание для сохранения
        ttl: Время жизни в секундах (по умолчанию из settings)
        
    Returns:
        True если успешно сохранено
    """
    if not REDIS_AVAILABLE:
        return False
    
    ttl = ttl or settings.REDIS_PREDICTION_CACHE_TTL
    
    try:
        cache_key = get_cache_key(features)
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(prediction)
        )
        return True
    except Exception as e:
        logger.warning(f"Ошибка записи в Redis: {e}")
        return False


def invalidate_cache(pattern: str = "ml_prediction:*") -> int:
    """
    Инвалидировать кэш по паттерну.
    
    Args:
        pattern: Паттерн для поиска ключей (по умолчанию все предсказания)
        
    Returns:
        Количество удаленных ключей
    """
    if not REDIS_AVAILABLE:
        return 0
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Ошибка инвалидации кэша: {e}")
        return 0

