"""
JanMitra – AI Assistant Service (Gemini-backed with Grounded Query-Specific Fallback)

Safety & response quality rules strictly enforced:
  - Answer the user's specific question first (no indiscriminate full scheme dumps)
  - Question-intent detection (benefits, documents, eligibility, application, deadline, etc.)
  - Never guarantee eligibility ("you may be eligible" / "आप पात्र हो सकते हैं" / "तुम्ही पात्र असू शकता")
  - Never fabricate scheme names, benefits, deadlines, or official links
  - Strictly grounded in verified official database context
  - Supports English, Hindi, and Marathi (including Hinglish)
  - Deterministic fallback when Gemini API key is missing
"""
import asyncio
import logging
import re
from typing import List, Optional, Dict, Any

from app.config import get_settings
from app.schemas.schemas import UserProfileInput
from app.ai.intent import (
    detect_intent,
    is_ambiguous_query,
    format_intent_response,
    INTENT_BENEFITS,
    INTENT_DOCUMENTS,
    INTENT_ELIGIBILITY,
    INTENT_APPLICATION,
    INTENT_DEADLINE,
    INTENT_AGE_INCOME,
    INTENT_STATUS,
    INTENT_OFFICIAL_LINK,
    INTENT_COMPARISON,
    INTENT_GENERAL,
)

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are JanMitra Assistant (जनमित्र सहाय्यक / जनमित्र सहायक), a knowledgeable, empathetic AI assistant created to help Indian citizens understand and access government schemes (सरकारी योजनाएं / शासकीय योजना).

LANGUAGE AND LOCALIZATION:
- You fully support English, Hindi (हिन्दी), and Marathi (मराठी).
- Always reply in the exact language in which the citizen contacted you:
  * English queries -> Clear, accessible English.
  * Hindi / Hinglish queries -> Natural, respectful Hindi (or natural Hinglish if preferred by user).
  * Marathi queries -> Fluent, respectful Marathi (Devanagari script).

STRICT QUERY-SPECIFIC RESPONSE RULES:
1. ANSWER THE USER'S EXACT QUESTION FIRST. Do NOT regurgitate the full scheme record if the user asked a specific question.
2. If asking about BENEFITS / FINANCIAL AID: Focus specifically on the financial amount, subsidies, or services provided.
3. If asking about REQUIRED DOCUMENTS: Provide the checklist of required documents only.
4. If asking about ELIGIBILITY: Explain the specific qualification criteria (age, income, occupation, category). Compare against user profile if provided. NEVER guarantee eligibility; always state "you may be eligible" / "आप पात्र हो सकते हैं" / "तुम्ही पात्र असू शकता".
5. If asking about HOW TO APPLY: Provide the step-by-step application instructions and the official application link.
6. If asking about LAST DATE / DEADLINE: If the scheme context contains an explicit deadline, state it. If no deadline is specified in the official database, clearly state that there is no fixed deadline in official records and that it is an ongoing welfare scheme. Never invent dates.
7. If asking about AGE OR INCOME LIMITS: State the exact age brackets and income thresholds only.
8. If asking a GENERAL QUESTION: Provide a concise 2-3 sentence overview followed by the main benefit.
9. If COMPARING SCHEMES: Compare only the requested schemes on relevant attributes.
10. If the question is broad or AMBIGUOUS matching multiple schemes: Briefly mention the top matching schemes and ask which one the citizen would like to know more about.

ACCURACY AND SAFETY:
- Never fabricate scheme names, monetary amounts, deadlines, or URLs. Rely strictly on the CONTEXT below.
- If specific information is not in the context, explicitly state: "I couldn't verify that specific detail from the available official government records."
- Never claim that an application has been submitted, approved, or processed. Application submission must always be completed on the official government portal.
- Always conclude with an indicative eligibility disclaimer.

DETECTED QUERY INTENT:
{detected_intent}

CONTEXT FROM OFFICIAL GOVERNMENT SCHEME DATABASE:
{scheme_context}

USER PROFILE (INDICATIVE):
{user_profile}
"""


def _build_scheme_context(scheme_data: Optional[List[dict]]) -> str:
    if not scheme_data:
        return "No specific scheme information retrieved for this query."

    parts = []

    for s in scheme_data:
        docs = s.get("documents")
        docs_str = ", ".join(docs) if isinstance(docs, list) and docs else "Standard KYC & income documents"

        occ = s.get("occupation")
        occ_str = ", ".join(occ) if isinstance(occ, list) and occ else "Any / Open to all"

        states = s.get("state")
        state_str = ", ".join(states) if isinstance(states, list) and states else "All India"

        # Safely handle missing income limits
        income_limit = s.get("income_limit")
        income_str = (
            f"₹{income_limit:,.0f} annually"
            if isinstance(income_limit, (int, float))
            else "Not specified"
        )

        part = f"""
Scheme: {s.get('name', '')}
Category: {s.get('category', 'General')}
Ministry / Department: {s.get('ministry') or s.get('department') or 'Government of India'}
Description: {s.get('description', '')}
Key Benefits: {s.get('benefits', 'Financial or social assistance as per official guidelines')}
Eligibility Criteria:
- Age: Min {s.get('min_age') or 'None'}, Max {s.get('max_age') or 'None'}
- Income Limit: {income_str}
- Gender: {s.get('gender') or 'Any'}
- Target Occupations: {occ_str}
- Target States: {state_str}
Documents Required: {docs_str}
How to Apply: {s.get('application_process') or 'Apply through the official portal'}
Official Application URL: {s.get('application_url') or 'See official portal'}
Official Source Portal: {s.get('official_source_url', 'https://www.myscheme.gov.in')}
Source Name: {s.get('source_name', 'Government of India')}
"""
        parts.append(part.strip())

    return "\n\n---\n\n".join(parts)


def _build_profile_context(profile: Optional[UserProfileInput]) -> str:
    if not profile:
        return "Profile not provided (Guest mode)."

    parts = []
    if profile.age:
        parts.append(f"Age: {profile.age} years")
    if profile.gender:
        parts.append(f"Gender: {profile.gender.capitalize()}")
    if profile.state:
        parts.append(f"State: {profile.state}")
    if profile.district:
        parts.append(f"District: {profile.district}")
    if profile.occupation:
        parts.append(f"Occupation: {profile.occupation.capitalize()}")
    if profile.annual_income is not None:
        if isinstance(profile.annual_income, (int, float)):
            parts.append(f"Annual Income: ₹{profile.annual_income:,.0f}")
        else:
            parts.append(f"Annual Income: {profile.annual_income}")
    if profile.category:
        parts.append(f"Social Category: {profile.category}")
    if profile.education:
        parts.append(f"Education: {profile.education}")
    if profile.disability:
        dis_info = f"Yes ({profile.disability_type})" if profile.disability_type else "Yes"
        parts.append(f"Disability: {dis_info}")
    if profile.marital_status:
        parts.append(f"Marital Status: {profile.marital_status.capitalize()}")

    return ", ".join(parts) if parts else "Guest user (no demographic details saved)."


def _detect_language(text: str) -> str:
    """Detect if text is predominantly Hindi, Marathi, or English."""
    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    if devanagari_chars > 2:
        marathi_words = ["आहे", "नाही", "माहिती", "योजना", "पात्रता", "मिळेल", "कागदपत्रे", "कसे", "करावे", "अर्ज", "फायदे"]
        for mw in marathi_words:
            if mw in text:
                return "mr"
        return "hi"

    text_lower = text.lower()
    tokens = set(re.findall(r"\w+", text_lower))

    # Common English conversational question tokens
    english_tokens = {"tell", "about", "what", "is", "how", "can", "am", "i", "which", "are", "details", "for"}
    if tokens & english_tokens and not (tokens & {"kya", "kaise", "aahe", "kasa", "kase", "batao", "sang", "mein", "milte", "kitne"}):
        return "en"

    # Transliterated Marathi detection
    marathi_markers = {"aahe", "mahiti", "patrata", "milel", "kagadpatre", "kase", "kasa", "arja", "sathi", "sang", "fayde", "yojaneche"}
    if tokens & marathi_markers:
        return "mr"

    # Transliterated Hindi detection
    hindi_markers = {"kya", "kaise", "patrata", "milega", "milte", "dastavej", "aavedan", "batao", "hai", "hoga", "mein", "paise", "kitne", "iski"}
    if tokens & hindi_markers:
        return "hi"

    return "en"


def _format_clarification_question(schemes: List[dict], lang: str) -> str:
    """Ask a clarifying question when multiple schemes match an ambiguous query."""
    lines = []
    for i, s in enumerate(schemes[:4], 1):
        lines.append(f"{i}. **{s.get('name')}** ({s.get('category')}) — {s.get('description', '')[:100]}…")
    options_text = "\n".join(lines)

    if lang == "hi":
        return (
            f"आपके प्रश्न से संबंधित कई सरकारी योजनाएं उपलब्ध हैं:\n\n"
            f"{options_text}\n\n"
            f"💡 **आप किस विशिष्ट योजना के बारे में जानना चाहते हैं?**\n"
            f"आप उस योजना के लाभ, पात्रता, आवश्यक दस्तावेज़ या आवेदन प्रक्रिया के बारे में पूछ सकते हैं।"
        )
    elif lang == "mr":
        return (
            f"आपल्या प्रश्नाशी संबंधित अनेक शासकीय योजना उपलब्ध आहेत:\n\n"
            f"{options_text}\n\n"
            f"💡 **आपण कोणत्या विशिष्ट योजनेबद्दल माहिती जाणून घेऊ इच्छिता?**\n"
            f"आपण संबंधित योजनेचे लाभ, पात्रता, कागदपत्रे किंवा अर्ज प्रक्रियेबद्दल विचारू शकता."
        )
    else:
        return (
            f"I found multiple government schemes matching your inquiry:\n\n"
            f"{options_text}\n\n"
            f"💡 **Which specific scheme would you like to explore?**\n"
            f"You can ask about its benefits, eligibility, required documents, or application process."
        )


def _generate_grounded_fallback(
    message: str,
    scheme_data: Optional[List[dict]],
    user_profile: Optional[UserProfileInput] = None,
) -> str:
    """
    High-accuracy, query-specific deterministic response when Gemini API key is missing
    or when external AI services are unreachable.
    """
    lang = _detect_language(message)

    if not scheme_data:
        if lang == "hi":
            return (
                "नमस्ते! जनमित्र में आपका स्वागत है। आपके प्रश्न से संबंधित कोई सरकारी योजना उपलब्ध आधिकारिक डेटाबेस में नहीं मिली।\n\n"
                "💡 **सुझाव:**\n"
                "• कृपया किसी विशिष्ट सरकारी योजना (जैसे: पीएम किसान, आयुष्मान भारत, पीएम आवास) का नाम लिखें।\n"
                "• अधिक जानकारी के लिए भारत सरकार के [myScheme.gov.in](https://www.myscheme.gov.in) पोर्टल पर जाएं।\n\n"
                "*(नोट: एआई मॉडल सक्रिय करने के लिए `backend/.env` में `GEMINI_API_KEY` सेट करें)*"
            )
        elif lang == "mr":
            return (
                "नमस्कार! जनमित्रमध्ये आपले स्वागत आहे. आपल्या प्रश्नाशी संबंधित कोणतीही शासकीय योजना उपलब्ध अधिकृत डेटाबेसमध्ये आढळली नाही.\n\n"
                "💡 **सल्ला:**\n"
                "• कृपया विशिष्ट योजनेचे नाव (उदा: पीएम किसान, आयुष्मान भारत, पीएम आवास) नमूद करा.\n"
                "• अधिक माहितीसाठी भारत सरकारच्या [myScheme.gov.in](https://www.myscheme.gov.in) पोर्टलला भेट द्या.\n\n"
                "*(टीप: AI मॉडेल सक्रिय करण्यासाठी `backend/.env` मध्ये `GEMINI_API_KEY` जोडा)*"
            )
        else:
            return (
                "Hello! Welcome to JanMitra. I could not find a government scheme directly matching your query in our official database.\n\n"
                "💡 **Suggestions:**\n"
                "• Please specify a known scheme (e.g. PM-KISAN, Ayushman Bharat, PM Awas Yojana) or ask about your occupation/state.\n"
                "• You can also browse the Schemes section or visit [myScheme.gov.in](https://www.myscheme.gov.in).\n\n"
                "*(Notice: Running in database-grounded mode. Configure `GEMINI_API_KEY` in `backend/.env` for generative AI)*"
            )

    # Check for ambiguity: multiple schemes matching a broad query without naming one
    if is_ambiguous_query(message, scheme_data):
        return _format_clarification_question(scheme_data, lang)

    # Detect specific query intent
    intent = detect_intent(message, len(scheme_data))
    primary_scheme = scheme_data[0]

    return format_intent_response(
        intent=intent,
        scheme=primary_scheme,
        user_profile=user_profile,
        lang=lang,
        all_schemes=scheme_data,
    )


async def get_ai_response(
    message: str,
    conversation_history: List[dict],
    scheme_data: Optional[List[dict]] = None,
    user_profile: Optional[UserProfileInput] = None,
) -> str:
    """
    Get a grounded AI response using Gemini with automatic query-intent handling.
    Falls back gracefully to deterministic query-specific answers if AI key is missing or fails.
    """
    if not settings.ai_available:
        logger.info("GEMINI_API_KEY not configured – serving grounded query-specific fallback")
        return _generate_grounded_fallback(message, scheme_data, user_profile)

    try:
        import google.generativeai as genai

        intent = detect_intent(message, len(scheme_data or []))
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            model_name=settings.ai_model,
            system_instruction=SYSTEM_PROMPT.format(
                detected_intent=intent,
                scheme_context=_build_scheme_context(scheme_data),
                user_profile=_build_profile_context(user_profile),
            ),
        )

        history = []
        for msg in conversation_history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = await asyncio.to_thread(
            chat.send_message,
            message,
            request_options={"timeout": 10},
        )
        if response and response.text:
            return response.text
        return _generate_grounded_fallback(message, scheme_data, user_profile)

    except ImportError:
        logger.warning("google-generativeai not installed")
        return _generate_grounded_fallback(message, scheme_data, user_profile)
    except Exception as e:
        logger.exception("Gemini API invocation error")
        return _generate_grounded_fallback(message, scheme_data, user_profile)
