import re


def generate_query(question: str) -> dict:
    text = question.lower().strip()

    # Low-stock inventory queries
    if any(word in text for word in [
        "low stock", "low in stock", "reorder",
        "need restocking", "below reorder"
    ]):
        return {
            "collection": "inventory",
            "filter": {
                "$expr": {
                    "$lte": ["$stock_quantity", "$reorder_level"]
                }
            },
            "description": "Find inventory at or below its reorder level"
        }

    # Category queries
    category_match = re.search(
        r"(?:in|under|within)\s+(?:the\s+)?"
        r"(electronics|furniture|clothing|food|accessories)"
        r"(?:\s+category)?",
        text
    )

    if category_match:
        category = category_match.group(1).title()
        return {
            "collection": "products",
            "filter": {"category": category},
            "description": f"Find products in the {category} category"
        }

    # Price greater than queries
    price_match = re.search(
        r"(?:more than|greater than|above|over|costing more than)"
        r"\s*(?:rs\.?|inr|₹)?\s*([\d,]+)",
        text
    )

    if price_match:
        price = int(price_match.group(1).replace(",", ""))
        return {
            "collection": "products",
            "filter": {"price": {"$gt": price}},
            "description": f"Find products priced above {price}"
        }

    # Price less than queries
    price_match = re.search(
        r"(?:less than|below|under|cheaper than)"
        r"\s*(?:rs\.?|inr|₹)?\s*([\d,]+)",
        text
    )

    if price_match:
        price = int(price_match.group(1).replace(",", ""))
        return {
            "collection": "products",
            "filter": {"price": {"$lt": price}},
            "description": f"Find products priced below {price}"
        }

    # Show all products
    if any(phrase in text for phrase in [
        "all products", "show products",
        "list products", "display products"
    ]):
        return {
            "collection": "products",
            "filter": {},
            "description": "List all products"
        }

    raise ValueError(
        "Question not recognized yet. Try asking about low stock, "
        "product category, product price, or all products."
    )
