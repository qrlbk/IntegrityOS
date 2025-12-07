"""
Настройка логирования для приложения.
"""
import logging
import sys
from pathlib import Path

# Настройка формата логов
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = "INFO"):
    """
    Настройка логирования для приложения.
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Получаем уровень логирования
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Настраиваем root logger
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Настраиваем логирование для SQLAlchemy (менее подробное)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Настраиваем логирование для uvicorn (менее подробное)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Логирование настроено с уровнем {log_level}")
    
    return logger


# Создаем logger для использования в приложении
logger = logging.getLogger("integrityos")


