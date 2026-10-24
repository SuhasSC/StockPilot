import json
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")

COLLECTION_FIELDS = {
    "products": {
        "product_id", "name", "category", "price",
        "description", "supplier_id", "created_date",
    },
    "inventory": {
        "product_id", "warehouse_id", "stock_quantity",
        "reorder_level", "location", "last_updated",
    },
    "sales": {
        "sale_id", "product_id", "product_name", "quantity",
        "unit_price", "total_amount", "sale_date", "city", "status",
    },
    "suppliers": {
        "supplier_record_id", "supplier_id", "name", "branch_id",
        "category_focus", "city", "state", "country", "email",
        "phone", "status", "created_date",
    },
}

ALLOWED_COLLECTIONS = set(COLLECTION_FIELDS)
ALLOWED_OPERATORS = {
    "$eq", "$ne", "$gt", "$gte", "$lt", "$lte",
    "$in", "$nin", "$and", "$or", "$expr",
}


def _validate_filter(value, allowed_fields, inside_expr=False):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.startswith("$"):
                if key not in ALLOWED_OPERATORS:
                    raise ValueError(f"Disallowed operator: {key}")
                if key == "$expr":
                    _validate_filter(child, allowed_fields, inside_expr=True)
                else:
                    _validate_filter(child, allowed_fields, inside_expr)
            elif inside_expr:
                if key not in {"$stock_quantity", "$reorder_level"}:
                    raise ValueError(f"Disallowed expression field: {key}")
                _validate_filter(child, allowed_fields, inside_expr=True)
            else:
                if key not in allowed_fields:
                    raise ValueError(f"Disallowed field: {key}")
                _validate_filter(child, allowed_fields, inside_expr=False)
    elif isinstance(value, list):
        for item in value:
            _validate_filter(item, allowed_fields, inside_expr)
    elif not isinstance(value, (str, int, float, bool)) and value is not None:
        raise ValueError("Unsupported query value.")


def generate_llm_query(question: str) -> dict:
    client = Groq()

    schema_text = "\n".join(
        f"{name}: {', '.join(sorted(fields))}"
        for name, fields in COLLECTION_FIELDS.items()
    )

    prompt = f"""
You are the natural-language query planner for StockPilot, an inventory
management application backed by MongoDB.

Understand the user's intent, not just exact keywords. Users may use:
- informal English, slang, abbreviations, or conversational wording;
- spelling mistakes or imperfect speech-to-text transcripts;
- different phrasings that mean the same thing;
- requests about stock, products, purchases/sales, suppliers, and locations.

Examples of intent:
- "what's running low?", "what are we nearly out of?", "what needs restocking?"
  mean inventory at or below its reorder level.
- "which stuff sold the most?" means rank or find sales by quantity. For a
  simple find query, return matching sales documents; do not claim to rank
  unless the query mechanism supports sorting.
- "who supplies the keyboards?" means find products matching the keyboard
  name, or supplier records if the user asks for supplier details. If a join
  between collections is needed, choose the most useful single collection
  and describe the limitation.
- "show completed sales in Mysuru" means sales filtered by status and city.
- "active suppliers" means suppliers filtered by status.

Database collections and exact fields:
{schema_text}

Rules:
- Return one JSON object with keys: collection, filter, description.
- Select exactly one collection from the schema above.
- Use only fields belonging to that selected collection.
- Use only MongoDB find filters and the approved operators:
  $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $and, $or, $expr.
- For low stock, use inventory and:
  {{"$expr": {{"$lte": ["$stock_quantity", "$reorder_level"]}}}}
- For all products, use products with an empty filter.
- For price questions, use products.price.
- For sales value questions, use sales.total_amount.
- For units sold, use sales.quantity.
- For city questions about sales, use sales.city.
- For supplier questions, use suppliers and its actual fields.
- Do not invent a price threshold, city, status, or other constraint the user
  did not provide.
- If a key detail is missing, prefer a broad safe filter and explain the
  ambiguity in description, rather than inventing details.
- Do not generate aggregation, sort, insert, update, delete, JavaScript,
  database commands, or arbitrary code.
- Never claim that data was found; this stage only creates a query.
- Preserve the meaning of the user's original language where possible.
- Return valid JSON only, with English JSON keys.

User question:
{question}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful MongoDB find-query planner. "
                    "Return valid JSON only and never invent schema fields."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=700,
        temperature=0,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("The LLM returned an empty response.")

    generated = json.loads(content)

    if generated.get("error") == "unsupported":
        raise ValueError("The question is not supported.")

    collection = generated.get("collection")
    if collection not in ALLOWED_COLLECTIONS:
        raise ValueError("The LLM selected a disallowed collection.")

    query_filter = generated.get("filter")
    if not isinstance(query_filter, dict):
        raise ValueError("The generated filter must be a JSON object.")

    _validate_filter(query_filter, COLLECTION_FIELDS[collection])

    return {
        "collection": collection,
        "filter": query_filter,
        "description": str(
            generated.get("description", "LLM-generated database query")
        )[:300],
    }
