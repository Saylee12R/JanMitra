"""
JanMitra – AI Assistant Service (Gemini-backed)

Safety rules enforced here:
  - Never guarantee eligibility
  - Never fabricate schemes, benefits, or URLs
  - Always cite database-sourced information
  - Graceful fallback if AI is unavailable
"""
import logging
from typing import List, Optional

from app.config import get_settings
from app.schemas.schemas import UserProfileInput

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are JanMitra Assistant, an AI assistant that helps Indian citizens discover and understand government schemes.

STRICT RULES:
1. NEVER guarantee that a user is eligible for a scheme. Always say "you may be eligible" or "based on the information provided".
2. NEVER fabricate scheme names, benefits, eligibility criteria, documents, application URLs, or government policies.
3. If you don't have information from the provided context, say: "I couldn't verify that information from the available official sources."
4. Always recommend checking official government portals for final confirmation.
5. Only cite schemes from the provided scheme context below.
6. Always add the disclaimer: "Final eligibility and application requirements should be confirmed on the official government website."

You are helpful, simple, and empathetic. Explain things in plain language that any citizen can understand.
If asked in Hindi or any Indian language, respond in that language.

CONTEXT FROM OFFICIAL DATABASE:
{scheme_context}

USER PROFILE:
{user_profile}
"""

FALLBACK_RESPONSES = {
    "default": (
        "I'm here to help you understand government schemes. "
        "Currently, the AI assistant is not configured. "
        "Please browse the schemes section to discover schemes relevant to your profile. "
        "Remember: always verify eligibility on official government portals."
    ),
    "schemes": (
        "To find schemes for you, please complete your profile by going to the onboarding section. "
        "Our eligibility engine will then match you with relevant government schemes. "
        "Final eligibility must be confirmed with the official scheme authority."
    ),
}


def _build_scheme_context(scheme_data: Optional[List[dict]]) -> str:
    if not scheme_data:
        return "No specific scheme information retrieved for this query."

    parts = []
    for s in scheme_data[:5]:  # limit context size
        part = f"""
Scheme: {s.get('name', '')}
Category: {s.get('category', '')}
Ministry: {s.get('ministry', '')}
Description: {s.get('description', '')}
Benefits: {s.get('benefits', 'Not specified')}
Documents Required: {', '.join(s.get('documents', [])) if s.get('documents') else 'Not specified'}
Application URL: {s.get('application_url', 'Check official website')}
Official Source: {s.get('official_source_url', '')}
"""
        parts.append(part)

    return "\n---\n".join(parts)


def _build_profile_context(profile: Optional[UserProfileInput]) -> str:
    if not profile:
        return "Profile not provided."

    parts = []
    if profile.age:
        parts.append(f"Age: {profile.age}")
    if profile.gender:
        parts.append(f"Gender: {profile.gender}")
    if profile.state:
        parts.append(f"State: {profile.state}")
    if profile.occupation:
        parts.append(f"Occupation: {profile.occupation}")
    if profile.annual_income is not None:
        parts.append(f"Annual Income: ₹{profile.annual_income:,.0f}")
    if profile.category:
        parts.append(f"Category: {profile.category}")
    if profile.education:
        parts.append(f"Education: {profile.education}")
    if profile.disability:
        parts.append("Has disability: Yes")

    return ", ".join(parts) if parts else "Limited profile information available."


async def get_ai_response(
    message: str,
    conversation_history: List[dict],
    scheme_data: Optional[List[dict]] = None,
    user_profile: Optional[UserProfileInput] = None,
) -> str:
    """
    Get a grounded AI response using Gemini.
    Falls back gracefully if AI is not configured.
    """
    if not settings.ai_available:
        logger.info("AI not configured – returning fallback response")
        return FALLBACK_RESPONSES["default"]

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name=settings.ai_model,
            system_instruction=SYSTEM_PROMPT.format(
                scheme_context=_build_scheme_context(scheme_data),
                user_profile=_build_profile_context(user_profile),
            ),
        )

        # Build conversation history
        history = []
        for msg in conversation_history[-10:]:  # last 10 messages for context
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = chat.send_message(message)
        return response.text

    except ImportError:
        logger.warning("google-generativeai not installed")
        return FALLBACK_RESPONSES["default"]
    except Exception as e:
        logger.error(f"AI error: {e}")
        return (
            "I apologize, I'm having trouble connecting right now. "
            "Please try again in a moment. "
            "For urgent queries, please visit the official government portal directly."
        )
