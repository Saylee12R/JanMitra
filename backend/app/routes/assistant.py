"""AI Assistant API routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Conversation, Message, Scheme, User, MessageRole
from app.schemas.schemas import ChatRequest, ChatResponse
from app.ai.assistant import get_ai_response
from app.ai.retrieval import retrieve_relevant_schemes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def _ensure_user_exists(user_id: int, db: Session) -> User:
    """Ensure user exists in DB to prevent foreign key errors."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        try:
            user = User(id=user_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            user = db.query(User).first()
            if not user:
                user = User()
                db.add(user)
                db.commit()
                db.refresh(user)
    return user


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
    # Ensure guest or provided user exists
    user_id = data.user_id if data.user_id and data.user_id > 0 else 1
    user = _ensure_user_exists(user_id, db)
    user_id = user.id

    # Get or create conversation
    conversation_id = data.conversation_id
    if not conversation_id:
        conv = Conversation(user_id=user_id, title=data.message[:100])
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conversation_id = conv.id
    else:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            conv = Conversation(user_id=user_id, title=data.message[:100])
            db.add(conv)
            db.commit()
            db.refresh(conv)
            conversation_id = conv.id

    # Load conversation history
    history = [
        {"role": m.role.value, "content": m.content}
        for m in db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).limit(20).all()
    ]
    logger.info(
    "CHAT HISTORY DEBUG: conversation_id=%s, history=%s",
    conversation_id,
    [(m["role"], m["content"]) for m in history]
)
    # Grounded RAG retrieval from verified database
    scheme_data = retrieve_relevant_schemes(
        query=data.message,
        db=db,
        user_profile=data.user_profile,
        conversation_history=history,
        limit=5,
    )

    # Get AI response (Gemini with grounded fallback)
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

    # Strictly filter sources to the scheme(s) actually discussed
    from app.ai.intent import detect_intent, INTENT_COMPARISON, is_ambiguous_query

    sources = []
    if scheme_data and not is_ambiguous_query(data.message, scheme_data):
        intent = detect_intent(data.message, len(scheme_data))
        if intent == INTENT_COMPARISON and len(scheme_data) >= 2:
            sources = [s.get("official_source_url") for s in scheme_data[:2] if s.get("official_source_url")]
        else:
            primary_url = scheme_data[0].get("official_source_url")
            if primary_url:
                sources = [primary_url]

    unique_sources = list(dict.fromkeys(sources))

    return ChatResponse(
        conversation_id=conversation_id,
        reply=reply,
        sources=unique_sources[:3],
        disclaimer=(
            "Information is retrieved from official government records. "
            "Final eligibility and application status must be confirmed with the official scheme authority."
        ),
    )
