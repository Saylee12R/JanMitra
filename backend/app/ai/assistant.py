"""
JanMitra – AI Assistant Service (Gemini-backed with Grounded Fallback)

Safety rules strictly enforced:
  - Never guarantee eligibility ("you may be eligible" / "आप पात्र हो सकते हैं" / "तुम्ही पात्र असू शकता")
  - Never fabricate scheme names, benefits, or official links
  - Strictly grounded in verified official database context
  - Supports English, Hindi, and Marathi
  - Deterministic fallback when Gemini API key is missing
"""
import logging
import re
from typing import List, Optional, Dict, Any

from app.config import get_settings
from app.schemas.schemas import UserProfileInput

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are JanMitra Assistant (जनमित्र सहाय्यक / जनमित्र सहायक), a trustworthy, knowledgeable, and empathetic AI assistant created to help Indian citizens discover, understand, and apply for government schemes (सरकारी योजनाएं / शासकीय योजना).

LANGUAGE AND LOCALIZATION:
- You fully support English, Hindi (हिन्दी), and Marathi (मराठी).
- Always reply in the language in which the citizen contacted you:
  * If the user writes in English -> Reply in clear, simple English.
  * If the user writes in Hindi (or Devanagari Hindi) -> Reply in natural, respectful Hindi.
  * If the user writes in Marathi (or Devanagari Marathi) -> Reply in fluent, respectful Marathi.
  * If the user uses Hinglish/transliteration, match their preference naturally.

STRICT ACCURACY AND SAFETY RULES:
1. NEVER GUARANTEE ELIGIBILITY: Government scheme criteria are strictly enforced by authorities. Always state that the applicant "may be eligible" ("आप पात्र हो सकते हैं" / "तुम्ही पात्र असू शकता") based on indicative criteria.
2. NEVER FABRICATE SCHEMES: Do not invent scheme names, monetary amounts, rules, or URLs. Rely strictly on the CONTEXT FROM OFFICIAL DATABASE below.
3. UNVERIFIED INFORMATION: If specific information (e.g. deadline, district center) is not in the context, explicitly state:
   - English: "I couldn't verify that specific detail from the available official government records."
   - Hindi: "उपलब्ध आधिकारिक सरकारी रिकॉर्ड से मैं इस विवरण की पुष्टि नहीं कर सका।"
   - Marathi: "उपलब्ध अधिकृत शासकीय माहितीवरून मी या तपशीलाची पुष्टी करू शकलो नाही."
4. NO FALSE SUBMISSION CLAIMS: Never claim that an application has been submitted, approved, or processed. Application submission must always be completed on the official government portal.
5. STRUCTURED CITIZEN GUIDANCE: Organize scheme explanations clearly:
   - **Scheme Overview**: What the scheme is and its core objective.
   - **Key Benefits**: Financial aid, subsidies, or services provided.
   - **Indicative Eligibility**: Who qualifies (age, income, occupation, category, state).
   - **Documents Required**: Checklist of required certificates and proofs.
   - **Application Process**: Step-by-step guidance and official application URL.
6. OFFICIAL SOURCES: Always cite the official source URL provided in the context.
7. MANDATORY DISCLAIMER: Always conclude with an indicative eligibility disclaimer.

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

        part = f"""
Scheme: {s.get('name', '')}
Category: {s.get('category', 'General')}
Ministry / Department: {s.get('ministry') or s.get('department') or 'Government of India'}
Description: {s.get('description', '')}
Key Benefits: {s.get('benefits', 'Financial or social assistance as per official guidelines')}
Eligibility Criteria:
  - Age: Min {s.get('min_age') or 'None'}, Max {s.get('max_age') or 'None'}
  - Income Limit: ₹{s.get('income_limit'):,.0f} annually if specified else 'None'
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
        parts.append(f"Annual Income: ₹{profile.annual_income:,.0f}")
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
    # Check for Devanagari script
    devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
    if devanagari_chars > 2:
        # Check specific Marathi vocabulary vs Hindi
        marathi_words = ["आहे", "नाही", "माहिती", "योजना", "पात्रता", "मिळेल", "कागदपत्रे", "कसे", "करावे", "अर्ज"]
        for mw in marathi_words:
            if mw in text:
                return "mr"
        return "hi"
    
    text_lower = text.lower()
    tokens = set(re.findall(r"\w+", text_lower))

    # Common English conversational question tokens
    english_tokens = {"tell", "about", "what", "is", "how", "can", "am", "i", "which", "are", "details", "for"}
    if tokens & english_tokens and not (tokens & {"kya", "kaise", "aahe", "kasa", "kase", "batao", "sang"}):
        return "en"

    # Transliterated Marathi detection
    marathi_markers = {"aahe", "mahiti", "patrata", "milel", "kagadpatre", "kase", "kasa", "arja", "sathi", "sang"}
    if tokens & marathi_markers:
        return "mr"

    # Transliterated Hindi detection
    hindi_markers = {"kya", "kaise", "patrata", "milega", "dastavej", "aavedan", "batao", "hai", "hoga"}
    if tokens & hindi_markers:
        return "hi"

    return "en"


def _generate_grounded_fallback(
    message: str,
    scheme_data: Optional[List[dict]],
    user_profile: Optional[UserProfileInput] = None,
) -> str:
    """
    High-accuracy, deterministic fallback response when Gemini API key is missing
    or when external AI services are temporarily unreachable.
    """
    lang = _detect_language(message)
    profile_summary = _build_profile_context(user_profile)

    if not scheme_data:
        if lang == "hi":
            return (
                "नमस्ते! जनमित्र में आपका स्वागत है। आपके प्रश्न से संबंधित कोई विशिष्ट योजना उपलब्ध आधिकारिक डेटाबेस में नहीं मिली।\n\n"
                "💡 **सुझाव:**\n"
                "• आप योजनाएं अनुभाग में जाकर श्रेणी और अपने व्यवसाय के अनुसार योजनाएं खोज सकते हैं।\n"
                "• आधिकारिक जानकारी के लिए कृपया भारत सरकार के [myScheme.gov.in](https://www.myscheme.gov.in) पोर्टल पर जाएं।\n\n"
                "*(नोट: एआई सेवा सक्रिय करने के लिए `backend/.env` में `GEMINI_API_KEY` सेट करें)*"
            )
        elif lang == "mr":
            return (
                "नमस्कार! जनमित्रमध्ये आपले स्वागत आहे. आपल्या प्रश्नाशी संबंधित विशिष्ट योजना उपलब्ध शासकीय डेटाबेसमध्ये आढळली नाही.\n\n"
                "💡 **सल्ला:**\n"
                "• आपण 'योजना' (Schemes) विभागात जाऊन आपल्या व्यवसाय व वर्गवारीनुसार योजना शोधू शकता.\n"
                "• अधिक माहितीसाठी कृपया भारत सरकारच्या अधिकृत [myScheme.gov.in](https://www.myscheme.gov.in) पोर्टलला भेट द्या.\n\n"
                "*(टीप: AI सहाय्यक सक्रिय करण्यासाठी `backend/.env` मध्ये `GEMINI_API_KEY` जोडा)*"
            )
        else:
            return (
                "Hello! Welcome to JanMitra. I could not find a specific scheme in our official database directly matching your query.\n\n"
                "💡 **Suggestions:**\n"
                "• Explore the **Schemes** tab to filter programs by category, state, and occupation.\n"
                "• Visit the official Government of India scheme portal at [myScheme.gov.in](https://www.myscheme.gov.in).\n\n"
                "*(Notice: JanMitra AI Assistant is in database-grounded mode. Configure `GEMINI_API_KEY` in `backend/.env` for interactive conversational answers)*"
            )

    # If scheme data exists, format a rich, structured answer from the top matched scheme
    primary_scheme = scheme_data[0]
    name = primary_scheme.get("name", "Government Scheme")
    category = primary_scheme.get("category", "General")
    ministry = primary_scheme.get("ministry") or primary_scheme.get("department") or "Government of India"
    description = primary_scheme.get("detailed_description") or primary_scheme.get("description", "")
    benefits = primary_scheme.get("benefits", "Direct benefit transfer / financial assistance as per official rules.")
    docs = primary_scheme.get("documents", [])
    docs_text = "\n".join([f"  • {d}" for d in docs]) if docs else "  • Aadhaar Card\n  • Bank Account Passbook\n  • Relevant Income / Category Proof"
    process = primary_scheme.get("application_process") or "Visit the official portal or nearest CSC/Seva Kendra to apply."
    app_url = primary_scheme.get("application_url") or primary_scheme.get("official_source_url") or "https://www.myscheme.gov.in"
    official_source = primary_scheme.get("official_source_url") or "https://www.myscheme.gov.in"

    if lang == "hi":
        return f"""यहाँ **{name}** ({category}) के संबंध में आधिकारिक सरकारी डेटाबेस से सत्यापित जानकारी दी गई है:

📋 **योजना का विवरण:**
{description}

💰 **प्रमुख लाभ:**
{benefits}

🎯 **पात्रता (संकेतात्मक):**
आपकी प्रोफाइल के आधार पर आप इस योजना के लिए पात्र हो सकते हैं। (न्यूनतम आयु: {primary_scheme.get('min_age') or 'लागू नहीं'}, अधिकतम आयु: {primary_scheme.get('max_age') or 'लागू नहीं'})।

📑 **आवश्यक दस्तावेज:**
{docs_text}

📝 **आवेदन प्रक्रिया:**
{process}
🔗 **आधिकारिक आवेदन लिंक:** [{app_url}]({app_url})
🌐 **आधिकारिक स्रोत:** [{official_source}]({official_source})

⚠️ *अस्वीकरण: यह जानकारी केवल मार्गदर्शन हेतु है। अंतिम पात्रता और नियमों की पुष्टि आधिकारिक पोर्टल पर करें।*

*(नोट: एआई मॉडल सक्रिय करने के लिए `backend/.env` में `GEMINI_API_KEY` सेट करें)*"""

    elif lang == "mr":
        return f"""**{name}** ({category}) बद्दल अधिकृत शासकीय डेटाबेसमधील सत्यापित माहिती खालीलप्रमाणे आहे:

📋 **योजनेचे स्वरूप:**
{description}

💰 **मिळणारे प्रमुख लाभ:**
{benefits}

🎯 **पात्रता निकष (मार्गदर्शक):**
आपल्या माहितीनुसार आपण या योजनेसाठी पात्र असू शकता. (किमान वय: {primary_scheme.get('min_age') or 'लागू नाही'}, कमाल वय: {primary_scheme.get('max_age') or 'लागू नाही'})।

📑 **आवश्यक कागदपत्रे:**
{docs_text}

📝 **अर्ज कसा करावा:**
{process}
🔗 **अधिकृत अर्ज लिंक:** [{app_url}]({app_url})
🌐 **शासकीय स्रोत:** [{official_source}]({official_source})

⚠️ *अस्वीकरण: ही माहिती केवळ मार्गदर्शनासाठी आहे. अंतिम पात्रता आणि नियमांची खात्री अधिकृत पोर्टलवर करावी.*

*(टीप: AI मॉडेल सक्रिय करण्यासाठी `backend/.env` मध्ये `GEMINI_API_KEY` जोडा)*"""

    else:
        return f"""Here is verified information regarding **{name}** from the official government database:

📋 **Overview:**
{description}

💰 **Key Benefits:**
{benefits}

🎯 **Indicative Eligibility:**
Based on standard guidelines, you may be eligible. (Age limit: {primary_scheme.get('min_age') or 'Any'} to {primary_scheme.get('max_age') or 'Any'} years; Income limit: {f"₹{primary_scheme.get('income_limit'):,.0f}" if primary_scheme.get('income_limit') else 'As per scheme rules'}).

📑 **Required Documents:**
{docs_text}

📝 **How to Apply:**
{process}
🔗 **Application Portal:** [{app_url}]({app_url})
🌐 **Official Source:** [{official_source}]({official_source})

⚠️ *Disclaimer: Indicative guidance only. Final eligibility must be confirmed with the official scheme authority.*

*(Notice: Running in database-grounded mode. Configure `GEMINI_API_KEY` in `backend/.env` for generative AI)*"""


async def get_ai_response(
    message: str,
    conversation_history: List[dict],
    scheme_data: Optional[List[dict]] = None,
    user_profile: Optional[UserProfileInput] = None,
) -> str:
    """
    Get a grounded AI response using Gemini with automatic multilingual capability.
    Falls back gracefully to deterministic scheme data if AI key is missing or fails.
    """
    if not settings.ai_available:
        logger.info("GEMINI_API_KEY not configured – serving grounded database fallback")
        return _generate_grounded_fallback(message, scheme_data, user_profile)

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
        for msg in conversation_history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = chat.send_message(message)
        if response and response.text:
            return response.text
        return _generate_grounded_fallback(message, scheme_data, user_profile)

    except ImportError:
        logger.warning("google-generativeai not installed")
        return _generate_grounded_fallback(message, scheme_data, user_profile)
    except Exception as e:
        logger.error(f"Gemini API invocation error: {e}")
        return _generate_grounded_fallback(message, scheme_data, user_profile)
