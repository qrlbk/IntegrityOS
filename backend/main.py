"""
Точка входа для запуска сервера.
Позволяет запускать: uvicorn backend.main:app --reload
"""
from app.main import app

__all__ = ["app"]


