"""
JanMitra – Lightweight RAG Retrieval Service

Performs grounded scheme retrieval from verified database records.
Optimized for government schemes with multi-field semantic scoring,
acronym resolution, and user profile boosting.
"""
import re
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

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

# Stopwords across English, Hindi, and Marathi transliteration
STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "what", "is", "are", "how", "can", "am", "i", "do", "does", "which", "tell", "me", "about",
    "kya", "hai", "ke", "ki", "ka", "ko", "se", "mein", "liye", "kaise", "kare", "koun",
    "kay", "aahe", "kasa", "kase", "sathi", "madhe", "ani", "kon", "kiti",
}


def _tokenize(text: str) -> List[str]:
    """Clean, lowercase, and tokenize query into search terms."""
    if not text:
        return []
    # Replace non-alphanumeric with spaces
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    tokens = [t.strip("-") for t in cleaned.split() if t.strip("-")]
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def retrieve_relevant_schemes(
    query: str,
    db: Session,
    user_profile: Optional[UserProfileInput] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve grounded scheme data for RAG context.
    
    Scores active schemes based on:
    - Acronym expansion match
    - Name and category match
    - Description and benefits match
    - Required documents match
    - Profile alignment (occupation, category, state)
    """
    tokens = _tokenize(query)
    
    # Expand acronyms if query matches
    query_lower = query.lower()
    for acr, expansion in ACRONYM_MAP.items():
        if acr in query_lower:
            tokens.extend(_tokenize(expansion))
    
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
        desc_lower = (scheme.description or "").lower()
        detailed_lower = (scheme.detailed_description or "").lower()
        benefits_lower = (scheme.benefits or "").lower()
        ministry_lower = (scheme.ministry or "").lower()
        category_lower = (scheme.category or "").lower()
        
        # Documents text
        docs_list = scheme.documents if isinstance(scheme.documents, list) else []
        docs_text = " ".join([str(d).lower() for d in docs_list])
        
        # Occupations text
        occ_list = scheme.occupation if isinstance(scheme.occupation, list) else []
        occ_text = " ".join([str(o).lower() for o in occ_list])

        # Exact substring in name (strong signal)
        for token in tokens:
            if token in name_lower:
                score += 15.0
            if token in category_lower:
                score += 8.0
            if token in ministry_lower:
                score += 5.0
            if token in desc_lower or token in detailed_lower:
                score += 4.0
            if token in benefits_lower:
                score += 4.0
            if token in docs_text:
                score += 3.0
            if token in occ_text:
                score += 5.0

        # Profile context boosting
        if user_profile:
            if user_profile.occupation:
                user_occ = user_profile.occupation.lower()
                if user_occ in occ_text or any(token in user_occ for token in tokens):
                    score += 6.0
            if user_profile.state and scheme.state:
                scheme_states = [s.lower() for s in scheme.state] if isinstance(scheme.state, list) else []
                if user_profile.state.lower() in scheme_states or "all" in scheme_states:
                    score += 3.0
            if user_profile.gender and scheme.gender:
                if scheme.gender.lower() in (user_profile.gender.lower(), "any", "all"):
                    score += 2.0

        if score > 0:
            scored_schemes.append((score, scheme))

    # If no tokens matched anything, return top active schemes as default context
    if not scored_schemes:
        # If user profile has occupation, prefer schemes for that occupation
        if user_profile and user_profile.occupation:
            user_occ = user_profile.occupation.lower()
            for s in active_schemes:
                s_occ = " ".join([str(o).lower() for o in (s.occupation or [])])
                if user_occ in s_occ:
                    scored_schemes.append((5.0, s))
        
        # Fallback to first few schemes if still empty
        if not scored_schemes:
            scored_schemes = [(1.0, s) for s in active_schemes[:limit]]

    # Sort descending by score
    scored_schemes.sort(key=lambda x: x[0], reverse=True)
    top_schemes = [s for _, s in scored_schemes[:limit]]

    # Convert to structured dictionary preserving official metadata
    results = []
    for s in top_schemes:
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
        })

    return results

