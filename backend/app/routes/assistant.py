"""AI Assistant API routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Conversation, Message, Scheme, User, MessageRole
from app.schemas.schemas import ChatRequest, ChatResponse
from app.ai.assistant import get_ai_response

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(data: ChatRequest, db: Session = Depends(get_db)):
    """
    AI-powered scheme assistant.

    Safety guarantees:
    - Does not guarantee eligibility
    - Does not fabricate scheme information
    - Cites only information from the official scheme database
    - Falls back gracefully if AI is unavailable
    """
    # Get or create conversation
    conversation_id = data.conversation_id
    if not conversation_id:
        # For guest mode, user_id may be None – use a placeholder
        user_id = data.user_id or 0
        conv = Conversation(user_id=user_id, title=data.message[:100])
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = conv.id
    else:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Load conversation history
    history = [
        {"role": m.role.value, "content": m.content}
        for m in db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).limit(20).all()
    ]

    # Find relevant schemes for context (simple keyword search)
    scheme_data = []
    keywords = data.message.lower().split()
    if keywords:
        schemes = db.query(Scheme).filter(Scheme.active == True).limit(100).all()
        relevant = []
        for s in schemes:
            score = 0
            for kw in keywords:
                if kw in s.name.lower() or kw in (s.description or "").lower():
                    score += 1
            if score > 0:
                relevant.append((score, s))
        relevant.sort(key=lambda x: x[0], reverse=True)
        scheme_data = [
            {
                "name": s.name,
                "category": s.category,
                "ministry": s.ministry,
                "description": s.description,
                "benefits": s.benefits,
                "documents": s.documents,
                "application_url": s.application_url,
                "official_source_url": s.official_source_url,
            }
            for _, s in relevant[:5]
        ]

    # Get AI response
    reply = await get_ai_response(
        message=data.message,
        conversation_history=history,
        scheme_data=scheme_data,
        user_profile=data.user_profile,
    )

    # Save messages
    user_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.user,
        content=data.message,
    )
    assistant_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.assistant,
        content=reply,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()

    sources = [s["official_source_url"] for s in scheme_data if s.get("official_source_url")]

    return ChatResponse(
        conversation_id=conversation_id,
        reply=reply,
        sources=sources[:3],
    )
