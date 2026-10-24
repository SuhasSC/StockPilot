import re

# Topics that clearly indicate a request outside inventory management.
UNRELATED_TOPIC_PATTERNS = [
    r"\bweather\b",
    r"\bforecast(?:ing)?\b",
    r"\bsports?\b",
    r"\bfootball\b",
    r"\bcricket\b",
    r"\bmovies?\b",
    r"\bactors?\b",
    r"\bpolitics?\b",
    r"\bcapital of\b",
    r"\bsolve (?:this )?equation\b",
]

INJECTION_PATTERNS = [
    r"\bignore (?:all |any )?(?:previous|prior|earlier) instructions\b",
    r"\bdrop (?:the )?(?:database|collection|table)\b",
    r"\bdelete (?:all |every )?(?:records|documents|products|sales)\b",
    r"\b(?:insert|update|remove) (?:into |all |every )?(?:the )?(?:database|collection|records|documents)\b",
]


def question_scope_error(question: str) -> str | None:
    """Reject clearly unrelated or command-like questions before query generation."""
    text = re.sub(r"\s+", " ", question.lower()).strip()

    if any(re.search(pattern, text) for pattern in INJECTION_PATTERNS):
        return "This request is not supported. Ask a read-only inventory question."

    if any(re.search(pattern, text) for pattern in UNRELATED_TOPIC_PATTERNS):
        return "This assistant supports inventory, products, stock, sales, and supplier questions."

    return None
