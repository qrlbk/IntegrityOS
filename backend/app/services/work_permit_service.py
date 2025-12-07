"""
Сервис для работы с нарядами-допусками.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.work_permit import WorkPermit, WorkPermitStatus
from app.core.logging_config import logger


def generate_permit_number(session: Session, issued_date: date) -> str:
    """
    Генерирует номер наряда-допуска в формате ND-YYYY-NNNN.
    
    Формат: ND-2025-0001, ND-2025-0002, и т.д.
    Нумерация начинается заново каждый год.
    
    Args:
        session: DB сессия
        issued_date: Дата выдачи наряда-допуска
        
    Returns:
        Строка с номером наряда-допуска (например, "ND-2025-0001")
    """
    year = issued_date.year
    
    # Находим последний номер для текущего года
    last_permit = (
        session.query(WorkPermit)
        .filter(extract('year', WorkPermit.issued_date) == year)
        .filter(WorkPermit.permit_number.like(f'ND-{year}-%'))
        .order_by(WorkPermit.permit_number.desc())
        .first()
    )
    
    if last_permit:
        # Извлекаем номер из последнего permit_number (например, "ND-2025-0042" -> 42)
        try:
            last_number = int(last_permit.permit_number.split('-')[-1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            # Если формат некорректный, начинаем с 1
            logger.warning(f"Не удалось извлечь номер из permit_number: {last_permit.permit_number}")
            next_number = 1
    else:
        # Первый наряд-допуск в этом году
        next_number = 1
    
    # Форматируем номер с ведущими нулями (4 цифры)
    permit_number = f"ND-{year}-{next_number:04d}"
    
    logger.info(f"Сгенерирован номер наряда-допуска: {permit_number}")
    return permit_number


def create_work_permit(
    session: Session,
    object_id: int,
    diagnostic_id: Optional[int] = None,
    issued_date: Optional[date] = None,
    issued_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> WorkPermit:
    """
    Создает новый наряд-допуск.
    
    Args:
        session: DB сессия
        object_id: ID объекта (внутренний id, не object_id из CSV)
        diagnostic_id: ID последней диагностики (опционально)
        issued_date: Дата выдачи (по умолчанию сегодня)
        issued_by: Кто выдал наряд-допуск
        notes: Дополнительные примечания
        
    Returns:
        Созданный WorkPermit объект
    """
    if issued_date is None:
        issued_date = date.today()
    
    # Генерируем номер наряда-допуска
    permit_number = generate_permit_number(session, issued_date)
    
    # Проверяем уникальность (на всякий случай)
    existing = session.query(WorkPermit).filter(WorkPermit.permit_number == permit_number).first()
    if existing:
        # Если номер уже существует (крайне маловероятно), добавляем суффикс
        permit_number = f"{permit_number}-{existing.permit_id}"
        logger.warning(f"Номер {permit_number} уже существует, добавлен суффикс")
    
    work_permit = WorkPermit(
        permit_number=permit_number,
        object_id=object_id,
        diagnostic_id=diagnostic_id,
        status=WorkPermitStatus.ISSUED.value,
        issued_date=issued_date,
        issued_by=issued_by,
        notes=notes,
    )
    
    session.add(work_permit)
    session.commit()
    session.refresh(work_permit)
    
    logger.info(f"Создан наряд-допуск {permit_number} для объекта {object_id}")
    return work_permit

