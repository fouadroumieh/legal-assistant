from __future__ import annotations
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone


# ---------------- Normalization ----------------
def _norm(s: Optional[str]) -> str:
    return (s or "").strip().lower()


# Canonical vocab & synonyms
AGREE_SYNONYMS = {
    "msa": "MSA",
    "master services agreement": "MSA",
    "nda": "NDA",
    "non disclosure": "NDA",
    "non-disclosure": "NDA",
    "sow": "SOW",
    "statement of work": "SOW",
    "dpa": "DPA",
    "data processing agreement": "DPA",
    "employment": "Employment",
}
INDUSTRY_SYNONYMS = {
    "tech": "Technology",
    "technology": "Technology",
    "it": "Technology",
    "software": "Technology",
    "healthcare": "Healthcare",
    "health care": "Healthcare",
    "finance": "Finance",
    "fintech": "Finance",
    "banking": "Finance",
    "manufacturing": "Manufacturing",
    "retail": "Retail",
    "ecommerce": "Retail",
    "e-commerce": "Retail",
}
LAW_SYNONYMS = {
    "us": "US",
    "usa": "US",
    "united states": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    "uk": "UK",
    "england": "UK",
    "uae": "UAE",
    "united arab emirates": "UAE",
    "ae": "UAE",
    "germany": "DE",
    "de": "DE",
    "deutschland": "DE",
    "south africa": "ZA",
    "za": "ZA",
}


def _canon_agreement(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    return AGREE_SYNONYMS.get(_norm(v), v)


def _canon_industry(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    return INDUSTRY_SYNONYMS.get(_norm(v), v)


def _canon_law(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    return LAW_SYNONYMS.get(_norm(v), v)


def _canon_field(field: str, v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    if field == "governing_law":
        return _canon_law(v)
    if field == "agreement_type":
        return _canon_agreement(v)
    if field == "industry":
        return _canon_industry(v)
    return v


# ---------------- Filter builders ----------------
def build_filters_from_question(q: str) -> dict:
    """
    High-trust extraction from the user's text; explicit words override NLP.
    Also treats bare country tokens as governing_law for short/empty queries.
    """
    qn = _norm(q)
    out: Dict[str, str] = {}

    # agreement_type
    for k, canon in AGREE_SYNONYMS.items():
        if k in qn:
            out["agreement_type"] = canon
            break

    # industry
    for k, canon in INDUSTRY_SYNONYMS.items():
        if k in qn:
            out["industry"] = canon
            break

    # governing_law – explicit mention first
    if "law" in qn or "governing" in qn:
        for k, canon in LAW_SYNONYMS.items():
            if k in qn:
                out["governing_law"] = canon
                break

    # If no governing_law yet, infer from bare country tokens for short/no-other-filter queries
    if "governing_law" not in out:
        tokens = qn.split()
        if len(tokens) <= 4 or not out:
            for k, canon in LAW_SYNONYMS.items():
                if k in qn:
                    out["governing_law"] = canon
                    break

    return out


def build_filters_from_nlp(nlp: dict, min_conf: float = 0.7) -> dict:
    """Best-effort from NLP with confidence gating (avoid spurious guesses)."""
    out: Dict[str, str] = {}

    # governing_law (accept as-is if present)
    gl = nlp.get("governing_law")
    if gl:
        out["governing_law"] = _canon_law(gl)

    # agreement_type with confidence
    at = nlp.get("agreement_type")
    at_conf = float(nlp.get("agreement_type_confidence") or 0.0)
    if at and at_conf >= min_conf:
        out["agreement_type"] = _canon_agreement(at)

    # industry with confidence
    ind = nlp.get("industry")
    ind_conf = float(nlp.get("industry_confidence") or 0.0)
    if ind and ind_conf >= min_conf:
        out["industry"] = _canon_industry(ind)

    return out


# ---------------- Matching ----------------
def _match(meta_value: Optional[str], want: Optional[str], field: str) -> bool:
    """Case-insensitive, partial-friendly, with field-specific canon on BOTH sides."""
    if not want:
        return True
    if not meta_value:
        return False
    mv = _canon_field(field, meta_value)
    w = _canon_field(field, want)
    mvn = _norm(mv)
    wn = _norm(w)
    return mvn == wn or mvn.startswith(wn) or wn in mvn


def matches(meta: dict, filters: dict) -> bool:
    """All provided fields must match; any subset of {agreement_type, industry, governing_law} is allowed."""
    for k, v in filters.items():
        if not _match(meta.get(k), v, k):
            return False
    return True


# ---------------- Context for NLP ----------------
def build_nlp_context(q: str) -> Dict[str, Any]:
    """Extra hints to guide NLP extraction; safe defaults if nothing fancy is available."""
    qn = _norm(q)
    now_iso = datetime.now(timezone.utc).isoformat()

    contains_law_word = any(
        w in qn for w in ("law", "governing", "under", "pursuant to")
    )
    contains_agreement_word = any(
        w in qn for w in ("agreement", "contract", "msa", "nda", "sow", "dpa")
    )
    contains_industry_word = any(
        w in qn
        for w in (
            "industry",
            "sector",
            "tech",
            "technology",
            "healthcare",
            "finance",
            "manufacturing",
            "retail",
        )
    )

    return {
        "domain": "legal_documents",
        "task": "extract_contract_filters",
        "fields": ["governing_law", "agreement_type", "industry"],
        "vocab": {
            "governing_law": ["US", "UK", "UAE", "DE", "ZA"],
            "agreement_type": ["MSA", "NDA", "SOW", "DPA", "Employment"],
            "industry": [
                "Technology",
                "Healthcare",
                "Finance",
                "Manufacturing",
                "Retail",
            ],
        },
        "hints": {
            "mentions_law": contains_law_word,
            "mentions_agreement": contains_agreement_word,
            "mentions_industry": contains_industry_word,
        },
        "locale": "en-US",
        "timezone": "Africa/Johannesburg",
        "timestamp": now_iso,
    }


# ---------------- Dynamo scan utility ----------------
def scan_all(table) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    start_key = None
    while True:
        kwargs = {}
        if start_key:
            kwargs["ExclusiveStartKey"] = start_key
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        start_key = resp.get("LastEvaluatedKey")
        if not start_key:
            break
    return items
