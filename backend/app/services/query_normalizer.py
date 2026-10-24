import re

# Common speech-recognition and typing errors for inventory terminology.
WORD_CORRECTIONS = {
    "salse": "sales",
    "salez": "sales",
    "inventry": "inventory",
    "inventery": "inventory",
    "suplier": "supplier",
    "supplir": "supplier",
    "suppiler": "supplier",
    "prodct": "product",
    "prodcuts": "products",
    "prducts": "products",
    "revanue": "revenue",
    "revinue": "revenue",
    "quanity": "quantity",
    "quantiy": "quantity",
    "catagory": "category",
    "categary": "category",
    "warehous": "warehouse",
    "restockng": "restocking",
    "restockingg": "restocking",
    "electornics": "electronics",
    "electonics": "electronics",
    "compeleted": "completed",
    "compleated": "completed",
    "karnatka": "karnataka",
    "mysuru city": "mysuru",
}

PHRASE_NORMALIZATIONS = [
    (r"\bwhat(?:'s| is) running low\b", "show low stock"),
    (r"\bwhat are we nearly out of\b", "show low stock"),
    (r"\bwhat needs restocking\b", "show low stock"),
    (r"\bitems? running out\b", "show low stock"),
    (r"\bnearly out of stock\b", "low stock"),
    (r"\bhow much did we make\b", "what is the total sales revenue"),
    (r"\bmoney made from sales\b", "total sales revenue"),
    (r"\bmonth wise revenue\b", "monthly revenue"),
    (r"\bmonthly sales revenue\b", "monthly revenue"),
    (r"\bsales city wise\b", "sales by city"),
    (r"\bcity wise sales\b", "sales by city"),
    (r"\bcategory wise products\b", "category summary"),
]


def normalize_question(question: str) -> str:
    """Lightly normalize common typos and phrases without rewriting intent."""
    text = question.strip().lower()
    text = re.sub(r"\s+", " ", text)

    for pattern, replacement in PHRASE_NORMALIZATIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    words = re.findall(r"\w+|\W+", text)
    normalized = []
    for token in words:
        if re.fullmatch(r"\w+", token):
            normalized.append(WORD_CORRECTIONS.get(token, token))
        else:
            normalized.append(token)

    return "".join(normalized).strip()
