"""
FastAPI приложение для IntegrityOS.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging_config import setup_logging
from app.core.exceptions import IntegrityOSException
from app.models import Pipeline, Object, Diagnostic, MLPredictionLog, WorkPermit  # Импорт для регистрации моделей
from app.api.v1 import objects, diagnostics, import_csv, ai_chat, analytics, ml_monitor, work_permits
# from app.api.v1 import ml  # ML роутер использует async, временно отключен

# Настраиваем логирование
logger = setup_logging(log_level="INFO")

# Создаем таблицы при старте (только для разработки)
# В продакшене используйте миграции Alembic
Base.metadata.create_all(bind=engine)
logger.info("База данных инициализирована")

app = FastAPI(
    title="IntegrityOS API",
    description="API для мониторинга магистральных трубопроводов",
    version="1.0.0",
)

# CORS middleware - должен быть первым
# В продакшене ограничьте origins конкретными доменами
cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"]
logger.info(f"CORS origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Список разрешенных доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы для разработки
    allow_headers=["*"],  # Разрешаем все заголовки для разработки
    expose_headers=["*"],  # Открываем все заголовки
    max_age=3600,  # Кэширование preflight запросов на 1 час
)


# Обработчик исключений (CORS middleware обработает заголовки автоматически)
@app.exception_handler(IntegrityOSException)
async def integrityos_exception_handler(request: Request, exc: IntegrityOSException):
    """Обработчик кастомных исключений IntegrityOS."""
    logger.error(f"IntegrityOS Exception: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "error_type": type(exc).__name__,
        },
    )
    # Убеждаемся, что CORS заголовки добавлены
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Обработчик HTTP исключений."""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации."""
    logger.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "error_type": "ValidationError",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик всех остальных исключений."""
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Внутренняя ошибка сервера: {str(exc)}",
            "error_type": type(exc).__name__,
        },
    )
    # Убеждаемся, что CORS заголовки добавлены
    return response

# Подключаем роутеры
app.include_router(objects.router, prefix="/api", tags=["objects"])
app.include_router(diagnostics.router, prefix="/api", tags=["diagnostics"])
app.include_router(import_csv.router, prefix="/api", tags=["import"])
app.include_router(ai_chat.router, prefix="/api", tags=["ai"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(ml_monitor.router, prefix="/api", tags=["ml-monitor"])
app.include_router(work_permits.router, prefix="/api", tags=["work-permits"])
# app.include_router(ml.router, prefix="/api/v1", tags=["ml"])  # ML роутер временно отключен


@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "IntegrityOS API", "version": "1.0.0"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
