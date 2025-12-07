"""
API endpoints для AI Assistant.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.services.ai_service import chat_with_ai

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    message: str
    context_used: bool
    error: Optional[str] = None


@router.post("/ai/chat", response_model=ChatResponse)
def chat(
    chat_message: ChatMessage,
    session: Session = Depends(get_db),
):
    """
    Чат с AI Assistant (RAG).
    
    Пользователь задает вопрос, AI отвечает на основе данных из базы.
    """
    try:
        result = chat_with_ai(
            session=session,
            user_message=chat_message.message,
            conversation_history=chat_message.conversation_history or []
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке запроса: {str(e)}"
        )


