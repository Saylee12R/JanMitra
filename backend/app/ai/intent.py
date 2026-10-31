"""
JanMitra – Query Intent Detection & Response Formatting

Identifies citizen question intent across English, Hindi, and Marathi (including Hinglish),
and generates query-specific, concise, grounded responses without dumping entire scheme records.
"""
import re
from types import SimpleNamespace
from typing import Dict, Any, List, Optional, Tuple

from app.services.eligibility import check_eligibility

INTENT_BENEFITS = "benefits"
INTENT_DOCUMENTS = "documents"
INTENT_ELIGIBILITY = "eligibility"
INTENT_APPLICATION = "application"
INTENT_DEADLINE = "deadline"
INTENT_AGE_INCOME = "age_income"
INTENT_STATUS = "status"
INTENT_OFFICIAL_LINK = "official_link"
INTENT_COMPARISON = "comparison"
INTENT_GENERAL = "general"

# Regex / token patterns for intent classification
PATTERNS = {
    INTENT_DEADLINE: [
        r"\b(last\s*date|deadline|end\s*date|closing\s*date|due\s*date|expiry|valid\s*(till|until))\b",
        r"\b(aakhri|akhri|antim)\s*(tarikh|tithi|dinank|date)\b",
        r"\b(shevatachi|shevat\s*chi|antim)\s*(tarikh|dinank|date)\b",
        r"\b(kab\s*tak|kadhiparyant|shevat)\b",
        r"(अंतिम|आखिरी|शेवटची)\s*(तारीख|तिथि|दिनांक|मुदत)",
        r"(कधीपर्यंत|मुदत)",
    ],
    INTENT_AGE_INCOME: [
        r"\b(age\s*limit|minimum\s*age|maximum\s*age|how\s*old|age\s*criteria|age\s*bracket)\b",
        r"\b(income\s*limit|maximum\s*income|annual\s*income|salary\s*limit|income\s*ceiling)\b",
        r"\b(aayu|umar|umra)\s*(seema|limit|kya)?\b",
        r"\b(aay|kamai|aamdani)\s*(seema|limit)\b",
        r"\b(vay|vaya)\s*(maryada|kiti)?\b",
        r"\b(utpanna|utpannachi)\s*(maryada|kiti)?\b",
        r"(वय\s*मर्यादा|उत्पन्नाची\s*मर्यादा|उत्पन्न\s*मर्यादा|आयु\s*सीमा|उम्र\s*सीमा|आय\s*सीमा)",
    ],
    INTENT_BENEFITS: [
        r"\b(paise|kitne\s*paise|kitna\s*paisa|kitna\s*rupya|kitne\s*milte|kitna\s*milega|kist|installment)\b",
        r"\b(kiti\s*paise|kiti\s*milnar|kiti\s*rakkam|kiti\s*labh|kiti\s*fayda)\b",
        r"\b(benefit|benefits|financial\s*aid|financial\s*assistance|money|amount|subsidy|subsidies|cashless|pension\s*amount)\b",
        r"\b(fayde|fayda|faayda|labh|sahayata|rashii|anudan)\b",
        r"(पैसे|रुपये|कितने\s*मिलते|कितना\s*मिलेगा|किती\s*मिळणार|लाभ|फायदे|फायदा|आर्थिक\s*सहाय्य|आर्थिक\s*मदत|हप्ता|रक्कम|अनुदान)",
    ],
    INTENT_DOCUMENTS: [
        r"\b(document|documents|doc|docs|paper|papers|certificate|certificates|proof|proofs)\b",
        r"\b(dastavej|dastawej|kagaz|kagajat|praman\s*patra|kya\s*lagega)\b",
        r"\b(kagadpatre|kagadpatra|pramanpatra|kay\s*lagel|dakhla|purava)\b",
        r"(दस्तावेज|दस्तावेज़|कागदपत्रे|कागदपत्र|कागजात|कागद|प्रमाणपत्र|दाखला|पुरावा|काय\s*लागेल|क्या\s*लगेगा)",
    ],
    INTENT_OFFICIAL_LINK: [
        r"\b(official\s*(link|website|portal|site|url)|portal\s*link|apply\s*link|link\s*kya|link\s*do|link\s*dya)\b",
        r"(अधिकृत\s*वेबसाईट|आधिकारिक\s*वेबसाइट|पोर्टल\s*लिंक|वेबसाइट\s*लिंक)",
    ],
    INTENT_APPLICATION: [
        r"\b(how\s*to\s*apply|application\s*process|procedure|steps\s*to\s*apply|where\s*to\s*apply|apply\s*online|registration|register)\b",
        r"\b(apply\s*kaise|aavedan\s*kaise|kaise\s*kare|kahan\s*se\s*apply|form\s*kaise|panjikaran)\b",
        r"\b(arja|arj|arji|kasa\s*karaycha|nodani\s*kashi|kothe\s*arja|kasa\s*karava|kasa\s*bharaycha)\b",
        r"(अर्ज|नोंदणी|आवेदन|आवेदन\s*कैसे\s*करें|आवेदन\s*प्रक्रिया|ऑनलाइन\s*अर्ज|फॉर्म\s*कसा)",
    ],
    INTENT_ELIGIBILITY: [
        r"\b(eligible|eligibility|qualify|qualification|criteria|who\s*can\s*apply|can\s*i\s*apply|am\s*i\s*eligible|can\s*we\s*apply)\b",
        r"\b(mere\s*liye|kisko\s*milega|kaun\s*apply|patra|patrata|yogyata|mil\s*sakta\s*hai)\b",
        r"\b(konala\s*milel|majhyasathi|patra\s*aahe\s*ka|milel\s*ka|kon\s*arja\s*karu\s*shakto)\b",
        r"(पात्रता|पात्र\s*आहे\s*का|पात्र\s*आहेत\s*का|कोणाला\s*मिळेल|कोन\s*पात्र|योग्यता|पात्रता\s*काय)",
    ],
    INTENT_STATUS: [
        r"\b(is\s*it\s*active|still\s*active|running|discontinued|closed|scheme\s*status)\b",
        r"\b(chalu\s*hai|chal\s*rahi\s*hai|band\s*ho\s*gayi|status\s*kya)\b",
        r"\b(chalu\s*aahe\s*ka|suru\s*aahe\s*ka|band\s*jhali\s*ka)\b",
        r"(चालू\s*आहे\s*का|सुरू\s*आहे\s*का|बंद\s*झाली\s*का|चालू\s*है\s*क्या|बंद\s*हो\s*गई)",
    ],
    INTENT_COMPARISON: [
        r"\b(compare|comparison|difference|versus|vs|better\s*between|which\s*is\s*better)\b",
        r"\b(dono.*(scheme|yojana|antar|farak|mein)|antar|farak|kisme\s*jyada|tulna)\b",
        r"\b(doghant\s*kay\s*farak|tulna|kay\s*farak)\b",
        r"(फरक|तुलना|अंतर|दोन्हीमध्ये\s*काय\s*फरक)",
    ],
}


def detect_intent(query: str, matched_schemes_count: int = 1) -> str:
    """
    Classify user query into a specific intent.
    Evaluates specific intents in priority order before defaulting to general.
    """
    q_lower = query.lower().strip()

    # If comparison explicitly indicated or multiple schemes mentioned
    for pattern in PATTERNS[INTENT_COMPARISON]:
        if re.search(pattern, q_lower):
            return INTENT_COMPARISON

    # Priority 1: Deadline / Last date questions
    for pattern in PATTERNS[INTENT_DEADLINE]:
        if re.search(pattern, q_lower):
            return INTENT_DEADLINE

    # Priority 2: Age / Income limit questions
    for pattern in PATTERNS[INTENT_AGE_INCOME]:
        if re.search(pattern, q_lower):
            return INTENT_AGE_INCOME

    # Priority 3: Benefits / Financial assistance questions
    for pattern in PATTERNS[INTENT_BENEFITS]:
        if re.search(pattern, q_lower):
            return INTENT_BENEFITS

    # Priority 4: Documents required questions
    for pattern in PATTERNS[INTENT_DOCUMENTS]:
        if re.search(pattern, q_lower):
            return INTENT_DOCUMENTS

    # Priority 5: Official Link / Portal URL questions
    for pattern in PATTERNS[INTENT_OFFICIAL_LINK]:
        if re.search(pattern, q_lower):
            return INTENT_OFFICIAL_LINK

    # Priority 6: How to Apply / Application process
    for pattern in PATTERNS[INTENT_APPLICATION]:
        if re.search(pattern, q_lower):
            return INTENT_APPLICATION

    # Priority 7: Eligibility questions
    for pattern in PATTERNS[INTENT_ELIGIBILITY]:
        if re.search(pattern, q_lower):
            return INTENT_ELIGIBILITY

    # Priority 8: Status questions (active / discontinued)
    for pattern in PATTERNS[INTENT_STATUS]:
        if re.search(pattern, q_lower):
            return INTENT_STATUS

    return INTENT_GENERAL


def is_ambiguous_query(query: str, schemes: List[Dict[str, Any]]) -> bool:
    """
    Check if a query is broad and matches multiple schemes without specifying a clear single scheme.
    Example: 'What scholarship schemes are available?' or 'loan schemes for me'
    """
    if len(schemes) < 2:
        return False

    q_lower = query.lower()
    # Check if a specific scheme name is in the query
    for s in schemes:
        name_lower = (s.get("name") or "").lower()
        slug_lower = (s.get("slug") or "").lower()
        # If user explicitly wrote the scheme's main title or slug, not ambiguous
        if slug_lower in q_lower or (len(name_lower) > 5 and name_lower in q_lower):
            return False

    # Check for broad category / type words
    broad_indicators = [
        "schemes", "yojana", "yojna", "yojane", "scholarships", "loans",
        "pensions", "options", "list", "available", "which schemes",
        "kaun si", "konte", "konte yojane", "konte labh", "kya kya"
    ]
    return any(ind in q_lower for ind in broad_indicators)


def _safe_format_currency(val: Any, default: str = "Not specified") -> str:
    """Format numeric value as INR currency safely without throwing NoneType formatting errors."""
    if val is None or val == "":
        return default
    try:
        num = float(val)
        return f"₹{num:,.0f}"
    except (ValueError, TypeError):
        return str(val)


def _safe_format_age(min_age: Any, max_age: Any) -> str:
    """Format age limits safely."""
    if min_age is not None and max_age is not None:
        return f"{min_age} to {max_age} years"
    elif min_age is not None:
        return f"Minimum {min_age} years"
    elif max_age is not None:
        return f"Up to {max_age} years"
    return "No specific age restrictions specified"


def format_intent_response(
    intent: str,
    scheme: Dict[str, Any],
    user_profile: Any = None,
    lang: str = "en",
    all_schemes: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Generate a query-specific, targeted response based on detected intent.
    Does NOT output irrelevant scheme sections.
    """
    name = scheme.get("name", "Government Scheme")
    category = scheme.get("category", "General")
    ministry = scheme.get("ministry") or scheme.get("department") or "Government of India"
    benefits = scheme.get("benefits") or "Financial assistance and welfare support as per official guidelines."
    docs = scheme.get("documents") or []
    process = scheme.get("application_process") or "Visit the official portal or designated service center (CSC) to apply."
    app_url = scheme.get("application_url") or scheme.get("official_source_url") or "https://www.myscheme.gov.in"
    official_source = scheme.get("official_source_url") or "https://www.myscheme.gov.in"
    min_age = scheme.get("min_age")
    max_age = scheme.get("max_age")
    income_limit = scheme.get("income_limit")
    active = scheme.get("active", True)

    # ─────────────────────────────────────────────────────────────
    # 1. BENEFITS INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_BENEFITS:
        if lang == "hi":
            return (
                f"**{name} — मिलने वाले लाभ एवं वित्तीय सहायता:**\n\n"
                f"💰 {benefits}\n\n"
                f"• **श्रेणी:** {category}\n"
                f"• **आधिकारिक स्रोत:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अस्वीकरण: लाभ का वितरण आधिकारिक नियमों व पात्रता सत्यापन के अधीन है।*"
            )
        elif lang == "mr":
            return (
                f"**{name} — मिळणारे लाभ आणि आर्थिक सहाय्य:**\n\n"
                f"💰 {benefits}\n\n"
                f"• **वर्गवारी:** {category}\n"
                f"• **शासकीय स्रोत:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अस्वीकरण: लाभ वितरण अधिकृत शासकीय नियमांनुसार आणि कागदपत्र पडताळणीनंतरच होते.*"
            )
        else:
            return (
                f"**{name} — Key Benefits & Financial Assistance:**\n\n"
                f"💰 {benefits}\n\n"
                f"• **Category:** {category}\n"
                f"• **Official Source:** [{official_source}]({official_source})\n\n"
                f"⚠️ *Disclaimer: Indicative guidance only. Benefit disbursement is subject to official verification.*"
            )

    # ─────────────────────────────────────────────────────────────
    # 2. DOCUMENTS INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_DOCUMENTS:
        if docs:
            docs_list_en = "\n".join([f"  • {d}" for d in docs])
        else:
            docs_list_en = "  • Aadhaar Card\n  • Bank Account Passbook\n  • Income / Caste Certificate (if applicable)"

        if lang == "hi":
            return (
                f"**{name} — आवश्यक दस्तावेज़:**\n\n"
                f"इस योजना के लिए निम्नलिखित दस्तावेजों की आवश्यकता है:\n"
                f"{docs_list_en}\n\n"
                f"• **आधिकारिक आवेदन लिंक:** [{app_url}]({app_url})\n\n"
                f"⚠️ *अस्वीकरण: आवेदन जमा करने से पहले आधिकारिक पोर्टल पर दस्तावेज़ सूची की पुष्टि करें।*"
            )
        elif lang == "mr":
            return (
                f"**{name} — आवश्यक कागदपत्रे:**\n\n"
                f"या योजनेसाठी खालील कागदपत्रे आवश्यक आहेत:\n"
                f"{docs_list_en}\n\n"
                f"• **अधिकृत अर्ज लिंक:** [{app_url}]({app_url})\n\n"
                f"⚠️ *अस्वीकरण: अंतिम अर्ज करण्यापूर्वी अधिकृत पोर्टलवरून कागदपत्रांची खात्री करावी.*"
            )
        else:
            return (
                f"**{name} — Required Documents:**\n\n"
                f"To apply for this scheme, the following documents are required:\n"
                f"{docs_list_en}\n\n"
                f"• **Official Application Portal:** [{app_url}]({app_url})\n\n"
                f"⚠️ *Disclaimer: Document checklists should be re-verified on the official portal prior to submission.*"
            )

    # ─────────────────────────────────────────────────────────────
    # 3. DEADLINE / LAST DATE INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_DEADLINE:
        if lang == "hi":
            return (
                f"**{name} — आवेदन की अंतिम तिथि (Deadline):**\n\n"
                f"उपलब्ध आधिकारिक सरकारी रिकॉर्ड में इस योजना के लिए **कोई निश्चित अंतिम तिथि (closing deadline) निर्धारित नहीं है**।\n"
                f"यह एक निरंतर (ongoing) कल्याणकारी योजना है, और इसके आवेदन सामान्यतः खुले रहते हैं।\n\n"
                f"• **वर्तमान चक्र व तिथियों की पुष्टि हेतु आधिकारिक पोर्टल देखें:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अस्वीकरण: विशेष वित्तीय वर्ष अथवा नामांकन चक्र की आधिकारिक सूचना पोर्टल पर देखें।*"
            )
        elif lang == "mr":
            return (
                f"**{name} — अर्ज करण्याची अंतिम मुदत (Deadline):**\n\n"
                f"उपलब्ध अधिकृत शासकीय नोंदीनुसार या योजनेसाठी **कोणतीही ठराविक अंतिम तारीख (closing deadline) निश्चित केलेली नाही**.\n"
                f"ही एक निरंतर (ongoing) कल्याणकारी योजना असून पात्र नागरिक सातत्याने अर्ज करू शकतात.\n\n"
                f"• **अधिकृत पोर्टलवरून सद्यस्थिती तपासा:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अस्वीकरण: चालू वर्षाच्या नावनोंदणी चक्राची माहिती अधिकृत संकेतस्थळावर तपासावी.*"
            )
        else:
            return (
                f"**{name} — Application Deadline:**\n\n"
                f"There is **no fixed closing date or deadline** specified in official records for this scheme.\n"
                f"It is an ongoing government welfare scheme with continuous enrollment for eligible citizens.\n\n"
                f"• **Verify current cycle on official portal:** [{official_source}]({official_source})\n\n"
                f"⚠️ *Disclaimer: Enrollment windows may vary by financial year or state batch. Confirm on official portal.*"
            )

    # ─────────────────────────────────────────────────────────────
    # 4. AGE & INCOME LIMIT INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_AGE_INCOME:
        age_str = _safe_format_age(min_age, max_age)
        income_str = f"{_safe_format_currency(income_limit)} annually" if income_limit else "No specific income ceiling specified"

        if lang == "hi":
            return (
                f"**{name} — आयु एवं आय सीमा:**\n\n"
                f"• **आयु सीमा (Age Limit):** {age_str}\n"
                f"• **वार्षिक आय सीमा (Income Limit):** {income_str}\n\n"
                f"• **आधिकारिक स्रोत:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अस्वीकरण: पात्रता नियमों की अंतिम पुष्टि आधिकारिक पोर्टल से करें।*"
            )
        elif lang == "mr":
            return (
                f"**{name} — वय व उत्पन्न मर्यादा:**\n\n"
                f"• **वय मर्यादा (Age Limit):** {age_str}\n"
                f"• **वार्षिक उत्पन्न मर्यादा (Income Limit):** {income_str}\n\n"
                f"• **शासकीय स्रोत:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अस्वीकरण: अंतिम पात्रतेची खात्री अधिकृत संकेतस्थळावरून करा.*"
            )
        else:
            return (
                f"**{name} — Age & Income Limits:**\n\n"
                f"• **Age Criteria:** {age_str}\n"
                f"• **Annual Income Limit:** {income_str}\n\n"
                f"• **Official Source:** [{official_source}]({official_source})\n\n"
                f"⚠️ *Disclaimer: Indicative limits from official records. Category-specific relaxations may apply.*"
            )

    # ─────────────────────────────────────────────────────────────
    # 5. APPLICATION PROCESS INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_APPLICATION:
        if lang == "hi":
            return (
                f"**{name} — आवेदन प्रक्रिया:**\n\n"
                f"📝 **आवेदन कैसे करें:**\n{process}\n\n"
                f"🔗 **आधिकारिक आवेदन लिंक:** [{app_url}]({app_url})\n"
                f"🌐 **आधिकारिक पोर्टल:** [{official_source}]({official_source})\n\n"
                f"⚠️ *महत्वपूर्ण: जनमित्र केवल मार्गदर्शन प्रदान करता है। आवेदन सीधे आधिकारिक सरकारी पोर्टल या सीएससी केंद्र पर जमा करें।*"
            )
        elif lang == "mr":
            return (
                f"**{name} — अर्ज प्रक्रिया:**\n\n"
                f"📝 **अर्ज कसा करावा:**\n{process}\n\n"
                f"🔗 **अधिकृत अर्ज लिंक:** [{app_url}]({app_url})\n"
                f"🌐 **शासकीय संकेतस्थळ:** [{official_source}]({official_source})\n\n"
                f"⚠️ *महत्त्वाचे: जनमित्र केवळ माहिती व मार्गदर्शन पुरवतो. अर्ज अधिकृत शासकीय पोर्टल किंवा सेवा केंद्रावरूनच करावा.*"
            )
        else:
            return (
                f"**{name} — How to Apply:**\n\n"
                f"📝 **Application Steps:**\n{process}\n\n"
                f"🔗 **Official Application Portal:** [{app_url}]({app_url})\n"
                f"🌐 **Scheme Information Portal:** [{official_source}]({official_source})\n\n"
                f"⚠️ *Important: JanMitra does not submit applications. Applications must be completed directly on the official government portal.*"
            )

    # ─────────────────────────────────────────────────────────────
    # 6. OFFICIAL LINK INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_OFFICIAL_LINK:
        if lang == "hi":
            return (
                f"**{name} — आधिकारिक लिंक:**\n\n"
                f"• **आवेदन पोर्टल:** [{app_url}]({app_url})\n"
                f"• **योजना दिशानिर्देश व स्रोत:** [{official_source}]({official_source})\n"
                f"• **मंत्रालय:** {ministry}\n\n"
                f"⚠️ *केवल आधिकारिक सरकारी (.gov.in / .nic.in) पोर्टलों पर ही अपनी व्यक्तिगत जानकारी दर्ज करें।*"
            )
        elif lang == "mr":
            return (
                f"**{name} — अधिकृत लिंक्स:**\n\n"
                f"• **अर्ज पोर्टल:** [{app_url}]({app_url})\n"
                f"• **शासकीय मार्गदर्शक व स्रोत:** [{official_source}]({official_source})\n"
                f"• **मंत्रालय:** {ministry}\n\n"
                f"⚠️ *केवळ अधिकृत शासकीय संकेतस्थळांवर (.gov.in / .nic.in) आपली माहिती नोंदवावी.*"
            )
        else:
            return (
                f"**{name} — Official Links:**\n\n"
                f"• **Application Portal:** [{app_url}]({app_url})\n"
                f"• **Official Information Source:** [{official_source}]({official_source})\n"
                f"• **Administering Ministry:** {ministry}\n\n"
                f"⚠️ *Always ensure you are accessing secure government domains (.gov.in / .nic.in).* "
            )

    # ─────────────────────────────────────────────────────────────
    # 7. ELIGIBILITY INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_ELIGIBILITY:
        occ = scheme.get("occupation")
        occ_str = ", ".join(occ) if isinstance(occ, list) and occ else "Open to all occupations"
        states = scheme.get("state")
        state_str = ", ".join(states) if isinstance(states, list) and states else "All India"
        age_info = _safe_format_age(min_age, max_age)
        income_info = f"Up to {_safe_format_currency(income_limit)} per year" if income_limit else "No specific income limit"

        profile_comparison = ""
        if user_profile:
            scheme_proxy = SimpleNamespace(
                min_age=scheme.get("min_age"),
                max_age=scheme.get("max_age"),
                gender=scheme.get("gender"),
                income_limit=scheme.get("income_limit"),
                occupation=scheme.get("occupation"),
                category_requirement=scheme.get("category_requirement"),
                state=scheme.get("state"),
                disability_required=scheme.get("disability_required"),
                education_requirement=scheme.get("education_requirement"),
                marital_status_requirement=scheme.get("marital_status_requirement"),
            )
            is_eligible, reasons, match_score = check_eligibility(scheme_proxy, user_profile)
            if is_eligible:
                reasons_str = "\n".join([f"  ✓ {r}" for r in reasons]) if reasons else "  ✓ All eligibility checks passed"
                if lang == "hi":
                    profile_comparison = (
                        f"\n\n**आपकी प्रोफ़ाइल के साथ मिलान (Deterministic Check):**\n"
                        f"• **स्थिति:** संभावित रूप से पात्र (मैच स्कोर: {match_score:.0f}%)\n"
                        f"{reasons_str}"
                    )
                elif lang == "mr":
                    profile_comparison = (
                        f"\n\n**आपल्या प्रोफाइलनुसार पात्रता (Deterministic Check):**\n"
                        f"• **स्थिती:** संभाव्य पात्र (मॅच स्कोअर: {match_score:.0f}%)\n"
                        f"{reasons_str}"
                    )
                else:
                    profile_comparison = (
                        f"\n\n**Your Profile Match (Deterministic Evaluation):**\n"
                        f"• **Status:** Potentially Eligible (Match Score: {match_score:.0f}%)\n"
                        f"{reasons_str}"
                    )
            else:
                if lang == "hi":
                    profile_comparison = (
                        f"\n\n**आपकी प्रोफ़ाइल के साथ मिलान (Deterministic Check):**\n"
                        f"• **स्थिति:** वर्तमान मानदंडों से मेल नहीं खाता (मैच स्कोर: 0%)\n"
                        f"  ℹ आपकी प्रोफ़ाइल का एक या अधिक विवरण इस योजना के पात्रता मानदंडों से बाहर है।"
                    )
                elif lang == "mr":
                    profile_comparison = (
                        f"\n\n**आपल्या प्रोफाइलनुसार पात्रता (Deterministic Check):**\n"
                        f"• **स्थिती:** निकषांनुसार अपात्र (मॅच स्कोअर: 0%)\n"
                        f"  ℹ आपल्या प्रोफाइलमधील माहिती या योजनेच्या पात्रता अटींशी जुळत नाही."
                    )
                else:
                    profile_comparison = (
                        f"\n\n**Your Profile Match (Deterministic Evaluation):**\n"
                        f"• **Status:** Outside Indicative Criteria (Match Score: 0%)\n"
                        f"  ℹ One or more profile attributes do not match this scheme's requirements."
                    )

        if lang == "hi":
            return (
                f"**{name} — पात्रता मानदंड:**\n\n"
                f"🎯 **पात्रता की मुख्य शर्तें:**\n"
                f"• **लक्षित वर्ग / व्यवसाय:** {occ_str}\n"
                f"• **आयु सीमा:** {age_info}\n"
                f"• **वार्षिक आय सीमा:** {income_info}\n"
                f"• **लागू राज्य:** {state_str}"
                f"{profile_comparison}\n\n"
                f"• **आधिकारिक स्रोत:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अस्वीकरण: आप पात्र हो सकते हैं। अंतिम पात्रता की पुष्टि आधिकारिक सरकारी प्राधिकरण द्वारा दस्तावेज़ सत्यापन के पश्चात की जाती है।*"
            )
        elif lang == "mr":
            return (
                f"**{name} — पात्रता निकष:**\n\n"
                f"🎯 **पात्रतेच्या प्रमुख अटी:**\n"
                f"• **लक्षित वर्ग / व्यवसाय:** {occ_str}\n"
                f"• **वय मर्यादा:** {age_info}\n"
                f"• **उत्पन्न मर्यादा:** {income_info}\n"
                f"• **लागू राज्ये:** {state_str}"
                f"{profile_comparison}\n\n"
                f"• **शासकीय स्रोत:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अस्वीकरण: उपलब्ध माहितीनुसार आपण पात्र असू शकता. अंतिम पात्रता अधिकृत शासकीय यंत्रणेद्वारे निश्चित केली जाते.*"
            )
        else:
            return (
                f"**{name} — Eligibility Criteria:**\n\n"
                f"🎯 **Core Criteria:**\n"
                f"• **Target Occupation / Group:** {occ_str}\n"
                f"• **Age Requirement:** {age_info}\n"
                f"• **Annual Income Ceiling:** {income_info}\n"
                f"• **Geographic Scope:** {state_str}"
                f"{profile_comparison}\n\n"
                f"• **Official Source:** [{official_source}]({official_source})\n\n"
                f"⚠️ *Disclaimer: You may be eligible based on indicative rules. Final eligibility must be confirmed with the official scheme authority.*"
            )

    # ─────────────────────────────────────────────────────────────
    # 8. STATUS INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_STATUS:
        st_text = "Active & Currently Operational" if active else "Inactive / Discontinued"
        verified_date = scheme.get("last_verified_at") or "Recently verified"
        if lang == "hi":
            return (
                f"**{name} — योजना की वर्तमान स्थिति:**\n\n"
                f"• **स्थिति (Status):** {st_text}\n"
                f"• **मंत्रालय:** {ministry}\n"
                f"• **सत्यापन तिथि:** {verified_date}\n"
                f"• **आधिकारिक पोर्टल:** [{official_source}]({official_source})\n\n"
                f"⚠️ *आधिकारिक पोर्टल से योजना की अद्यतन स्थिति अवश्य जांचें।*"
            )
        elif lang == "mr":
            return (
                f"**{name} — योजनेची सद्यस्थिती:**\n\n"
                f"• **स्थिती (Status):** {st_text}\n"
                f"• **मंत्रालय:** {ministry}\n"
                f"• **सत्यापन दिनांक:** {verified_date}\n"
                f"• **अधिकृत पोर्टल:** [{official_source}]({official_source})\n\n"
                f"⚠️ *अधिक माहितीसाठी अधिकृत शासकीय संकेतस्थळाला भेट द्यावी.*"
            )
        else:
            return (
                f"**{name} — Current Scheme Status:**\n\n"
                f"• **Status:** {st_text}\n"
                f"• **Administering Ministry:** {ministry}\n"
                f"• **Last Verified:** {verified_date}\n"
                f"• **Official Portal:** [{official_source}]({official_source})\n\n"
                f"⚠️ *Disclaimer: Always verify live status directly on the official portal.*"
            )

    # ─────────────────────────────────────────────────────────────
    # 9. COMPARISON INTENT
    # ─────────────────────────────────────────────────────────────
    if intent == INTENT_COMPARISON and all_schemes and len(all_schemes) >= 2:
        s1 = all_schemes[0]
        s2 = all_schemes[1]
        n1, n2 = s1.get("name", "Scheme 1"), s2.get("name", "Scheme 2")
        b1, b2 = s1.get("benefits", "N/A"), s2.get("benefits", "N/A")
        c1, c2 = s1.get("category", "General"), s2.get("category", "General")
        u1, u2 = s1.get("application_url") or s1.get("official_source_url"), s2.get("application_url") or s2.get("official_source_url")

        if lang == "hi":
            return (
                f"**तुलना: {n1} बनाम {n2}**\n\n"
                f"| विवरण | {n1} | {n2} |\n"
                f"|---|---|---|\n"
                f"| **श्रेणी** | {c1} | {c2} |\n"
                f"| **प्रमुख लाभ** | {b1} | {b2} |\n"
                f"| **पोर्टल** | [{u1}]({u1}) | [{u2}]({u2}) |\n\n"
                f"⚠️ *अस्वीकरण: दोनों योजनाओं के विस्तृत नियम व पात्रता संबंधित आधिकारिक पोर्टलों पर देखें।*"
            )
        elif lang == "mr":
            return (
                f"**तुलना: {n1} आणि {n2}**\n\n"
                f"| तपशील | {n1} | {n2} |\n"
                f"|---|---|---|\n"
                f"| **वर्गवारी** | {c1} | {c2} |\n"
                f"| **प्रमुख लाभ** | {b1} | {b2} |\n"
                f"| **पोर्टल** | [{u1}]({u1}) | [{u2}]({u2}) |\n\n"
                f"⚠️ *अस्वीकरण: अधिकृत माहितीसाठी वरील पोर्टलला भेट द्यावी.*"
            )
        else:
            return (
                f"**Comparison: {n1} vs {n2}**\n\n"
                f"| Feature | {n1} | {n2} |\n"
                f"|---|---|---|\n"
                f"| **Category** | {c1} | {c2} |\n"
                f"| **Benefits** | {b1} | {b2} |\n"
                f"| **Official Portal** | [{u1}]({u1}) | [{u2}]({u2}) |\n\n"
                f"⚠️ *Disclaimer: Indicative comparison. Specific eligibility rules apply to each scheme individually.*"
            )

    # ─────────────────────────────────────────────────────────────
    # 10. GENERAL INTENT (CONCISE OVERVIEW)
    # ─────────────────────────────────────────────────────────────
    desc = scheme.get("description") or "A central welfare scheme of the Government of India."
    if lang == "hi":
        return (
            f"**{name} ({category}):**\n\n"
            f"📋 **संक्षिप्त विवरण:** {desc}\n\n"
            f"💰 **प्रमुख लाभ:** {benefits}\n\n"
            f"🔗 **आधिकारिक पोर्टल:** [{official_source}]({official_source})\n\n"
            f"💡 *आप विशिष्ट प्रश्न पूछ सकते हैं, जैसे: पात्रता, आवश्यक दस्तावेज़, अंतिम तिथि या आवेदन प्रक्रिया।*\n\n"
            f"⚠️ *अस्वीकरण: यह जानकारी केवल मार्गदर्शन हेतु है।*"
        )
    elif lang == "mr":
        return (
            f"**{name} ({category}):**\n\n"
            f"📋 **थोडक्यात माहिती:** {desc}\n\n"
            f"💰 **प्रमुख लाभ:** {benefits}\n\n"
            f"🔗 **शासकीय पोर्टल:** [{official_source}]({official_source})\n\n"
            f"💡 *आपण विशिष्ट प्रश्न विचारू शकता, जसे की: पात्रता, कागदपत्रे, अंतिम मुदत किंवा अर्ज कसा करावा.*\n\n"
            f"⚠️ *अस्वीकरण: ही माहिती केवळ मार्गदर्शनासाठी आहे.*"
        )
    else:
        return (
            f"**{name} ({category}):**\n\n"
            f"📋 **Overview:** {desc}\n\n"
            f"💰 **Primary Benefit:** {benefits}\n\n"
            f"🔗 **Official Portal:** [{official_source}]({official_source})\n\n"
            f"💡 *You can ask specific questions such as: required documents, eligibility, deadline, or how to apply.*\n\n"
            f"⚠️ *Disclaimer: Indicative guidance only. Verify details on the official portal.*"
        )
