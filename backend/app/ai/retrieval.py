"""
JanMitra – Lightweight RAG Retrieval Service

Performs grounded scheme retrieval from verified database records.
Optimized for government schemes with multi-field semantic scoring,
acronym resolution, conversation context awareness, and user profile boosting.
"""
import re
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import Scheme
from app.schemas.schemas import UserProfileInput

logger = logging.getLogger(__name__)

# Common acronyms mapped to full scheme keywords
ACRONYM_MAP = {
    "pmkisan": "pm kisan samman nidhi farmer",
    "pm-kisan": "pm kisan samman nidhi farmer",
    "kisan": "kisan farmer krishi",
    "pmay": "pradhan mantri awas yojana housing",
    "awas": "awas housing",
    "ayushman": "ayushman bharat pmjay health insurance",
    "pmjay": "ayushman bharat pmjay health insurance",
    "mgnrega": "mgnrega nrega rural employment guarantee job",
    "nrega": "mgnrega nrega rural employment guarantee job",
    "ujjwala": "pradhan mantri ujjwala lpg gas connection",
    "sukanya": "sukanya samriddhi girl child savings",
    "mudra": "pradhan mantri mudra loan business enterprise",
    "apy": "atal pension yojana pension old age",
    "atal": "atal pension yojana pension",
    "svanidhi": "pm svanidhi street vendor loan",
    "scholarship": "scholarship student education post matric pre matric",
    "pension": "pension old age senior citizen retirement",
    "ration": "ration card food security nfsa grain",
    "ladli": "ladli behna beti girl child women",
}

# Devanagari keywords mapped to English/transliterated scheme tokens
DEVANAGARI_MAP = {
    "किसान": "kisan farmer",
    "पीएम": "pm",
    "योजना": "yojana scheme",
    "आयुष्मान": "ayushman health",
    "आवास": "awas housing",
    "उज्ज्वला": "ujjwala gas",
    "सुकन्या": "sukanya",
    "मुद्रा": "mudra loan",
    "पेंशन": "pension",
    "आरोग्य": "arogya health",
    "रोजगार": "employment nrega",
    "नरेगा": "nrega mgnrega",
    "मनरेगा": "mgnrega",
    "विद्यार्थी": "student scholarship",
    "शिष्यवृत्ती": "scholarship",
    "छात्रवृत्ति": "scholarship",
    "शेतकरी": "farmer kisan",
}

# Stopwords across English, Hindi, and Marathi transliteration
STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "what", "is", "are", "how", "can", "am", "i", "do", "does", "which", "tell", "me", "about",
    "kya", "hai", "ke", "ki", "ka", "ko", "se", "mein", "liye", "kaise", "kare", "koun", "kitna", "kitne",
    "kay", "aahe", "kasa", "kase", "sathi", "madhe", "ani", "kon", "kiti", "dya", "batao", "milta", "milte",
    "paise", "paisa", "rupaye", "documents", "dastavej", "kagadpatre", "tarikh", "date", "status", "eligible",
    "meri", "mera", "mere", "majhi", "majha", "majhe", "apna", "apni", "apne", "karo", "check",
}


def _tokenize(text: str) -> List[str]:
    """Clean, lowercase, and tokenize query into search terms."""
    if not text:
        return []
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    tokens = [t.strip("-") for t in cleaned.split() if t.strip("-")]
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def _extract_recent_scheme_name(history: Optional[List[dict]]) -> Optional[str]:
    """Inspect previous messages to find scheme discussed if current query uses pronouns or follow-up terms."""
    if not history:
        return None
    # Sort acronyms by length descending so longer/more specific names match first (e.g. pm-kisan before kisan)
    sorted_acrs = sorted(ACRONYM_MAP.keys(), key=len, reverse=True)
    # Check backwards through conversation history
    for msg in reversed(history):
        content = msg.get("content", "").lower()
        for acr in sorted_acrs:
            pattern = r"(?<!\w)" + re.escape(acr) + r"(?!\w)"
            if re.search(pattern, content):
                return acr
    return None


def _extract_explicit_scheme_from_query(query: str) -> Optional[str]:
    """Check if query explicitly mentions a known scheme acronym or key name."""
    q_lower = query.lower()
    sorted_acrs = sorted(ACRONYM_MAP.keys(), key=len, reverse=True)
    for acr in sorted_acrs:
        pattern = r"(?<!\w)" + re.escape(acr) + r"(?!\w)"
        if re.search(pattern, q_lower):
            return acr
    return None


def retrieve_relevant_schemes(
    query: str,
    db: Session,
    user_profile: Optional[UserProfileInput] = None,
    conversation_history: Optional[List[dict]] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve grounded scheme data for RAG context.
    
    Scores active schemes based on:
    - Scheme name and acronym match
    - Category and ministry match
    - Description & occupation match
    - Conversation history context (for pronouns like 'is scheme ke...')
    - Profile alignment (occupation, category, state)
    """
    tokens = _tokenize(query)
    query_lower = query.lower()

    # Check Devanagari mappings
    for dev_term, exp in DEVANAGARI_MAP.items():
        if dev_term in query:
            tokens.extend(_tokenize(exp))

    # Expand acronyms if query matches
    for acr, expansion in ACRONYM_MAP.items():
        if acr in query_lower:
            tokens.extend(_tokenize(expansion))

    # 1. Check if current query explicitly specifies a scheme
    explicit_scheme = _extract_explicit_scheme_from_query(query)

    # 2. Check if this is a follow-up query relying on conversation history
    followup_markers = [
        "is scheme", "this scheme", "iski", "iska", "iske",
        "ya yojane", "hyache", "yojana", "tarihi", "apply kaise",
        "eligible", "eligibility", "patra", "patrata", "yogyata", "mere liye",
        "documents", "dastavej", "kagadpatre", "last date", "deadline", "tarikh",
        "aavedan", "arja", "paise", "fayde", "labh", "benefits", "status"
    ]

    is_followup = (not explicit_scheme) and any(m in query_lower for m in followup_markers)

    if is_followup:
        prev_scheme = _extract_recent_scheme_name(conversation_history)
        if prev_scheme:
            matching_schemes = [
                scheme for scheme in db.query(Scheme).filter(Scheme.active == True).all()
                if prev_scheme in (scheme.name or "").lower()
                or prev_scheme in (scheme.slug or "").lower()
            ]

            if matching_schemes:
                s = matching_schemes[0]
                return [{
                    "id": s.id,
                    "name": s.name,
                    "slug": s.slug,
                    "category": s.category,
                    "ministry": s.ministry,
                    "department": s.department,
                    "description": s.description,
                    "detailed_description": s.detailed_description,
                    "min_age": s.min_age,
                    "max_age": s.max_age,
                    "income_limit": s.income_limit,
                    "gender": s.gender,
                    "occupation": s.occupation,
                    "category_requirement": s.category_requirement,
                    "state": s.state,
                    "education_requirement": s.education_requirement,
                    "benefits": s.benefits,
                    "documents": s.documents,
                    "application_process": s.application_process,
                    "application_url": s.application_url,
                    "official_source_url": s.official_source_url,
                    "source_name": s.source_name,
                    "last_verified_at": s.last_verified_at.isoformat() if s.last_verified_at else None,
                    "active": s.active,
                }]

    # Deduplicate tokens
    tokens = list(dict.fromkeys(tokens))

    # Query all active schemes
    active_schemes = db.query(Scheme).filter(Scheme.active == True).all()
    if not active_schemes:
        return []

    scored_schemes = []

    for scheme in active_schemes:
        score = 0.0
        name_lower = (scheme.name or "").lower()
        slug_lower = (scheme.slug or "").lower()
        desc_lower = (scheme.description or "").lower()
        benefits_lower = (scheme.benefits or "").lower()
        ministry_lower = (scheme.ministry or "").lower()
        category_lower = (scheme.category or "").lower()
        
        occ_list = scheme.occupation if isinstance(scheme.occupation, list) else []
        occ_text = " ".join([str(o).lower() for o in occ_list])

        # Exact slug or full title substring in query -> highest relevance
        if slug_lower in query_lower or name_lower in query_lower:
            score += 35.0

        for token in tokens:
            pattern = r"(?<!\w)" + re.escape(token) + r"(?!\w)"
            if re.search(pattern, name_lower) or re.search(pattern, slug_lower):
                score += 15.0
            if re.search(pattern, category_lower):
                score += 8.0
            if re.search(pattern, ministry_lower):
                score += 5.0
            if re.search(pattern, occ_text):
                score += 5.0
            if re.search(pattern, desc_lower):
                score += 2.0
            if re.search(pattern, benefits_lower):
                score += 2.0

        # Profile context boosting only if query is relevant or general
        if user_profile and score > 0:
            if user_profile.occupation:
                user_occ = user_profile.occupation.lower()
                if user_occ in occ_text:
                    score += 4.0
            if user_profile.state and scheme.state:
                scheme_states = [s.lower() for s in scheme.state] if isinstance(scheme.state, list) else []
                if user_profile.state.lower() in scheme_states or "all" in scheme_states:
                    score += 2.0

        if score > 0:
            scored_schemes.append((score, scheme))

    # Profile matching fallback when user asks about schemes for themselves
    profile_recs_words = [
        "my profile", "mere liye", "majhyasathi", "for me", "recommend",
        "suggest", "suitable", "can i get", "i get", "for my", "schemes can",
        "available for", "schemes for", "what schemes",
    ]
    if not scored_schemes and user_profile:
        if any(w in query_lower for w in profile_recs_words) or len(tokens) == 0:
            if user_profile.occupation:
                user_occ = user_profile.occupation.lower()
                for s in active_schemes:
                    s_occ = " ".join([str(o).lower() for o in (s.occupation or [])])
                    if user_occ in s_occ:
                        scored_schemes.append((8.0, s))

    # If still no scored schemes, return empty list (do not invent or return unrelated schemes)
    if not scored_schemes:
        return []

    # Sort descending by score
    scored_schemes.sort(key=lambda x: x[0], reverse=True)

    # If top scheme is very strong and specific, avoid returning unrelated trailing schemes
    top_score = scored_schemes[0][0]
    filtered_schemes = []
    for sc, sch in scored_schemes[:limit]:
        # Keep if within reasonable ratio of top score or score is substantial
        if sc >= top_score * 0.4 or sc >= 10.0:
            filtered_schemes.append(sch)
        elif len(filtered_schemes) == 0:
            filtered_schemes.append(sch)

    # Convert to structured dictionary preserving official metadata
    results = []
    for s in filtered_schemes:
        results.append({
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "category": s.category,
            "ministry": s.ministry,
            "department": s.department,
            "description": s.description,
            "detailed_description": s.detailed_description,
            "min_age": s.min_age,
            "max_age": s.max_age,
            "income_limit": s.income_limit,
            "gender": s.gender,
            "occupation": s.occupation,
            "category_requirement": s.category_requirement,
            "state": s.state,
            "education_requirement": s.education_requirement,
            "benefits": s.benefits,
            "documents": s.documents,
            "application_process": s.application_process,
            "application_url": s.application_url,
            "official_source_url": s.official_source_url,
            "source_name": s.source_name,
            "last_verified_at": s.last_verified_at.isoformat() if s.last_verified_at else None,
            "active": s.active,
        })

    return results
