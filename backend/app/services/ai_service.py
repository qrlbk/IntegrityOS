"""
Сервис для работы с AI Assistant (RAG).
"""
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.object import Object
from app.models.diagnostic import Diagnostic
from app.models.pipeline import Pipeline
from app.core.config import settings

try:
    from openai import OpenAI
    
    # Инициализируем клиент OpenAI
    # Проверяем наличие ключа в настройках
    openai_key = getattr(settings, 'OPENAI_API_KEY', None) or ""
    openai_key = openai_key.strip() if openai_key else ""
    
    # Создаем клиент только если ключ есть и валиден
    if openai_key and openai_key.startswith('sk-') and len(openai_key) > 20:
        client = OpenAI(api_key=openai_key)
        print("✅ OpenAI клиент инициализирован успешно.")
    else:
        client = None
        print("⚠️  OpenAI API ключ не найден или невалиден. AI Assistant требует OpenAI API ключ.")
except ImportError:
    client = None
    print("⚠️  OpenAI библиотека не установлена. Установите: pip install openai")
except Exception as e:
    client = None
    print(f"⚠️  Ошибка инициализации OpenAI клиента: {e}")


def get_context_for_ai(session: Session, query: str) -> str:
    """
    Собирает контекст из базы данных для RAG.
    
    Args:
        session: DB сессия
        query: Запрос пользователя
        
    Returns:
        Строка с контекстом
    """
    context_parts = []
    
    # Анализируем запрос для определения что нужно
    query_lower = query.lower()
    
    # Статистика по трубопроводам
    pipelines = session.query(Pipeline).all()
    context_parts.append(f"\n## Трубопроводы ({len(pipelines)} шт):")
    for pipeline in pipelines:
        objects = session.query(Object).filter(Object.pipeline_id == pipeline.id).all()
        critical_count = sum(1 for obj in objects if any(
            diag.defect_found for diag in session.query(Diagnostic)
            .filter(Diagnostic.object_id == obj.id)
            .order_by(desc(Diagnostic.date))
            .limit(5)
            .all()
        ))
        context_parts.append(f"- {pipeline.name}: {len(objects)} объектов, {critical_count} критических")
    
    # Если запрос про конкретную трассу
    if any(pipeline.name.lower() in query_lower for pipeline in pipelines):
        for pipeline in pipelines:
            if pipeline.name.lower() in query_lower:
                objects = session.query(Object).filter(Object.pipeline_id == pipeline.id).all()
                critical_objects = []
                
                for obj in objects:
                    diagnostics = (
                        session.query(Diagnostic)
                        .filter(Diagnostic.object_id == obj.id)
                        .filter(Diagnostic.defect_found == True)
                        .order_by(desc(Diagnostic.date))
                        .limit(3)
                        .all()
                    )
                    if diagnostics:
                        critical_objects.append({
                            "name": obj.object_name,
                            "type": obj.object_type.value,
                            "lat": obj.lat,
                            "lon": obj.lon,
                            "defects": [
                                {
                                    "date": diag.date.isoformat(),
                                    "method": diag.method.value,
                                    "description": diag.defect_description or "Дефект обнаружен"
                                }
                                for diag in diagnostics
                            ]
                        })
                
                if critical_objects:
                    context_parts.append(f"\n## Критические объекты на трассе {pipeline.name}:")
                    for obj in critical_objects[:10]:  # Ограничиваем количество
                        context_parts.append(f"- {obj['name']} ({obj['type']}): {len(obj['defects'])} дефектов")
                        if obj['defects']:
                            latest = obj['defects'][0]
                            context_parts.append(f"  Последний дефект: {latest['date']} ({latest['method']}) - {latest['description']}")
    
    # Общая статистика
    total_objects = session.query(Object).count()
    critical_objects_count = sum(1 for obj in session.query(Object).all() if any(
        diag.defect_found for diag in session.query(Diagnostic)
        .filter(Diagnostic.object_id == obj.id)
        .order_by(desc(Diagnostic.date))
        .limit(5)
        .all()
    ))
    total_diagnostics = session.query(Diagnostic).count()
    
    context_parts.insert(0, f"## Общая статистика:\n- Всего объектов: {total_objects}\n- Критических объектов: {critical_objects_count}\n- Всего диагностик: {total_diagnostics}")
    
    return "\n".join(context_parts)


def chat_with_ai(session: Session, user_message: str, conversation_history: List[Dict] = None) -> Dict:
    """
    Обрабатывает сообщение пользователя с помощью AI.
    
    Args:
        session: DB сессия
        user_message: Сообщение пользователя
        conversation_history: История разговора
        
    Returns:
        Ответ AI
    """
    # Проверяем, что OpenAI клиент инициализирован
    if client is None:
        return {
            "message": "OpenAI API ключ не настроен. Пожалуйста, добавьте OPENAI_API_KEY в файл .env и перезапустите сервер.",
            "context_used": False,
            "error": "OpenAI client not initialized"
        }
    
    # Собираем контекст
    context = get_context_for_ai(session, user_message)
    
    # Формируем промпт с контекстом
    system_prompt = """Ты AI-ассистент системы мониторинга магистральных трубопроводов IntegrityOS. 
Твоя задача - помогать инженерам анализировать данные диагностики и находить критические участки.

Отвечай кратко, профессионально и по делу. Используй только данные из контекста.
Если в контексте нет нужной информации, скажи об этом.

Формат ответа:
- Краткое описание ситуации
- Конкретные рекомендации
- Упомяни конкретные объекты/трассы если они есть в контексте"""
    
    user_prompt = f"""Контекст из базы данных:
{context}

Вопрос пользователя: {user_message}

Ответь на вопрос пользователя, используя контекст выше."""
    
    try:
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Добавляем историю если есть
        if conversation_history:
            for msg in conversation_history[-5:]:  # Последние 5 сообщений
                messages.append({"role": "user", "content": msg.get("user", "")})
                messages.append({"role": "assistant", "content": msg.get("assistant", "")})
        
        messages.append({"role": "user", "content": user_prompt})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Более быстрая и дешевая модель
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            "message": response.choices[0].message.content,
            "context_used": True
        }
    except Exception as e:
        # Возвращаем ошибку от OpenAI API
        error_msg = str(e)
        if "api key" in error_msg.lower() or "authentication" in error_msg.lower():
            return {
                "message": "Ошибка аутентификации OpenAI API. Проверьте правильность API ключа в .env файле.",
                "context_used": False,
                "error": error_msg
            }
        return {
            "message": f"Ошибка OpenAI API: {error_msg}",
            "context_used": False,
            "error": error_msg
        }

