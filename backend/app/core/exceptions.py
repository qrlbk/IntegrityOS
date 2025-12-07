"""
Кастомные исключения для приложения.
"""
from fastapi import HTTPException, status


class IntegrityOSException(Exception):
    """Базовое исключение для IntegrityOS."""
    pass


class DatabaseError(IntegrityOSException):
    """Ошибка работы с базой данных."""
    pass


class ImportError(IntegrityOSException):
    """Ошибка импорта данных."""
    pass


class MLModelError(IntegrityOSException):
    """Ошибка работы с ML моделью."""
    pass


def create_http_exception(
    status_code: int,
    detail: str,
    error_type: str = None
) -> HTTPException:
    """
    Создает HTTPException с дополнительной информацией.
    
    Args:
        status_code: HTTP статус код
        detail: Детали ошибки
        error_type: Тип ошибки (опционально)
    """
    error_detail = {"detail": detail}
    if error_type:
        error_detail["error_type"] = error_type
    
    return HTTPException(status_code=status_code, detail=error_detail)


