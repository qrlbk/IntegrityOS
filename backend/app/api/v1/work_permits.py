"""
API endpoints для нарядов-допусков.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict
from datetime import date as date_type

from app.core.database import get_db
from app.models.work_permit import WorkPermit, WorkPermitStatus
from app.models.object import Object
from app.models.diagnostic import Diagnostic
from app.schemas.work_permit import (
    WorkPermitCreate,
    WorkPermitUpdate,
    WorkPermitResponse,
    WorkPermitListItem,
)
from app.services.work_permit_service import create_work_permit
from app.core.logging_config import logger

router = APIRouter()


@router.post("/work-permits", response_model=WorkPermitResponse)
def create_work_permit_endpoint(
    work_permit: WorkPermitCreate,
    session: Session = Depends(get_db),
):
    """
    Создает новый наряд-допуск.
    
    Args:
        work_permit: Данные для создания наряда-допуска
        session: DB сессия
    """
    # Проверяем существование объекта
    # Важно: object_id здесь - это внутренний id, а не object_id из CSV
    obj = session.query(Object).filter(Object.id == work_permit.object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Object with id={work_permit.object_id} not found")
    
    # Если указан diagnostic_id, проверяем его существование
    if work_permit.diagnostic_id:
        diag = session.query(Diagnostic).filter(Diagnostic.diag_id == work_permit.diagnostic_id).first()
        if not diag:
            raise HTTPException(status_code=404, detail=f"Diagnostic with id={work_permit.diagnostic_id} not found")
        # Проверяем, что диагностика принадлежит объекту
        if diag.object_id != work_permit.object_id:
            raise HTTPException(
                status_code=400,
                detail=f"Diagnostic {work_permit.diagnostic_id} does not belong to object {work_permit.object_id}"
            )
    
    # Создаем наряд-допуск
    permit = create_work_permit(
        session=session,
        object_id=work_permit.object_id,
        diagnostic_id=work_permit.diagnostic_id,
        issued_date=work_permit.issued_date,
        issued_by=work_permit.issued_by,
        notes=work_permit.notes,
    )
    
    return permit


@router.post("/work-permits/create-for-object/{object_id}", response_model=WorkPermitResponse)
def create_work_permit_for_object(
    object_id: int,  # object_id из CSV (видимый пользователю)
    issued_by: Optional[str] = None,
    notes: Optional[str] = None,
    session: Session = Depends(get_db),
):
    """
    Создает наряд-допуск для объекта, автоматически используя последнюю диагностику.
    
    Args:
        object_id: ID объекта из CSV (не внутренний id)
        issued_by: Кто выдал наряд-допуск
        notes: Дополнительные примечания
        session: DB сессия
    """
    # Находим объект по object_id из CSV
    obj = session.query(Object).filter(Object.object_id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Object with object_id={object_id} not found")
    
    # Находим последнюю диагностику
    last_diagnostic = (
        session.query(Diagnostic)
        .filter(Diagnostic.object_id == obj.id)
        .order_by(desc(Diagnostic.date))
        .first()
    )
    
    diagnostic_id = last_diagnostic.diag_id if last_diagnostic else None
    
    # Создаем наряд-допуск
    permit = create_work_permit(
        session=session,
        object_id=obj.id,  # Используем внутренний id
        diagnostic_id=diagnostic_id,
        issued_date=date_type.today(),
        issued_by=issued_by,
        notes=notes,
    )
    
    return permit


@router.get("/work-permits", response_model=List[WorkPermitListItem])
def get_work_permits(
    object_id: Optional[int] = Query(None, description="Фильтр по ID объекта из CSV"),
    status: Optional[str] = Query(None, description="Фильтр по статусу (issued/active/closed/cancelled)"),
    limit: Optional[int] = Query(100, description="Максимальное количество записей"),
    sort_by: Optional[str] = Query("issued_date", description="Сортировка: issued_date, permit_number"),
    sort_order: Optional[str] = Query("desc", description="Порядок сортировки: asc или desc"),
    session: Session = Depends(get_db),
):
    """
    Возвращает список нарядов-допусков с фильтрацией.
    """
    query = session.query(WorkPermit).join(Object)
    
    # Фильтр по object_id из CSV
    if object_id:
        query = query.filter(Object.object_id == object_id)
    
    # Фильтр по статусу
    if status:
        query = query.filter(WorkPermit.status == status)
    
    # Сортировка
    if sort_by == "issued_date":
        if sort_order == "desc":
            query = query.order_by(desc(WorkPermit.issued_date))
        else:
            query = query.order_by(asc(WorkPermit.issued_date))
    elif sort_by == "permit_number":
        if sort_order == "desc":
            query = query.order_by(desc(WorkPermit.permit_number))
        else:
            query = query.order_by(asc(WorkPermit.permit_number))
    
    # Лимит
    if limit:
        query = query.limit(limit)
    
    permits = query.all()
    
    # Формируем результат
    result = []
    for permit in permits:
        result.append({
            "permit_id": permit.permit_id,
            "permit_number": permit.permit_number,
            "object_id": permit.object.object_id,  # Используем object_id из CSV
            "object_name": permit.object.object_name,
            "status": permit.status,
            "issued_date": permit.issued_date.isoformat(),
            "issued_by": permit.issued_by,
            "closed_date": permit.closed_date.isoformat() if permit.closed_date else None,
        })
    
    return result


@router.get("/work-permits/{permit_id}", response_model=WorkPermitResponse)
def get_work_permit(
    permit_id: int,
    session: Session = Depends(get_db),
):
    """
    Возвращает информацию о конкретном наряде-допуске.
    """
    permit = session.query(WorkPermit).filter(WorkPermit.permit_id == permit_id).first()
    if not permit:
        raise HTTPException(status_code=404, detail=f"Work permit with id={permit_id} not found")
    
    return permit


@router.get("/work-permits/by-number/{permit_number}", response_model=WorkPermitResponse)
def get_work_permit_by_number(
    permit_number: str,
    session: Session = Depends(get_db),
):
    """
    Возвращает информацию о наряде-допуске по его номеру.
    """
    permit = session.query(WorkPermit).filter(WorkPermit.permit_number == permit_number).first()
    if not permit:
        raise HTTPException(status_code=404, detail=f"Work permit with number={permit_number} not found")
    
    return permit


@router.get("/work-permits/for-object/{object_id}", response_model=List[WorkPermitListItem])
def get_work_permits_for_object(
    object_id: int,  # object_id из CSV
    session: Session = Depends(get_db),
):
    """
    Возвращает все наряды-допуски для объекта.
    """
    obj = session.query(Object).filter(Object.object_id == object_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Object with object_id={object_id} not found")
    
    permits = (
        session.query(WorkPermit)
        .filter(WorkPermit.object_id == obj.id)
        .order_by(desc(WorkPermit.issued_date))
        .all()
    )
    
    result = []
    for permit in permits:
        result.append({
            "permit_id": permit.permit_id,
            "permit_number": permit.permit_number,
            "object_id": object_id,
            "object_name": permit.object.object_name,
            "status": permit.status,
            "issued_date": permit.issued_date.isoformat(),
            "issued_by": permit.issued_by,
            "closed_date": permit.closed_date.isoformat() if permit.closed_date else None,
        })
    
    return result


@router.patch("/work-permits/{permit_id}", response_model=WorkPermitResponse)
def update_work_permit(
    permit_id: int,
    update_data: WorkPermitUpdate,
    session: Session = Depends(get_db),
):
    """
    Обновляет наряд-допуск (статус, дата закрытия и т.д.).
    """
    permit = session.query(WorkPermit).filter(WorkPermit.permit_id == permit_id).first()
    if not permit:
        raise HTTPException(status_code=404, detail=f"Work permit with id={permit_id} not found")
    
    # Обновляем поля
    if update_data.status:
        permit.status = update_data.status
    if update_data.closed_date:
        permit.closed_date = update_data.closed_date
    if update_data.closed_by:
        permit.closed_by = update_data.closed_by
    if update_data.notes is not None:
        permit.notes = update_data.notes
    
    session.commit()
    session.refresh(permit)
    
    return permit

