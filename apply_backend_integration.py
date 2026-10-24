from pathlib import Path

path = Path(r"backend/app/api/routes.py")
source = path.read_text(encoding="utf-8")
original = source

# 1. Import the question normalizer.
old_import = "from app.services.aggregation_generator import generate_aggregation_query"
new_import = old_import + "\nfrom app.services.query_normalizer import normalize_question"

if "from app.services.query_normalizer import normalize_question" not in source:
    if old_import not in source:
        raise SystemExit("ERROR: Could not find the aggregation import.")
    source = source.replace(old_import, new_import, 1)

# 2. Validate field references inside expressions such as $expr.
old_scalar = '''    elif not isinstance(value, (str, int, float, bool)) and value is not None:
        raise ValueError("Unsupported query value.")'''

new_scalar = '''    elif isinstance(value, str) and inside_expr and value.startswith("$"):
        if value[1:] not in allowed_fields:
            raise ValueError("Disallowed expression field reference.")
    elif not isinstance(value, (str, int, float, bool)) and value is not None:
        raise ValueError("Unsupported query value.")'''

if old_scalar in source:
    source = source.replace(old_scalar, new_scalar, 1)
elif new_scalar not in source:
    raise SystemExit("ERROR: Could not find the filter validator ending.")

# 3. Permit the planner's specific monthly grouping expression.
old_group = '''            elif group_id is not None:
                raise ValueError("Unsupported group identifier.")'''

new_group = '''            elif isinstance(group_id, dict):
                # Only allow the exact month extraction expression used by
                # the trusted monthly-revenue planner.
                if set(group_id) != {"$substrCP"}:
                    raise ValueError("Unsupported group identifier.")

                args = group_id["$substrCP"]
                if (
                    collection_name != "sales"
                    or not isinstance(args, list)
                    or len(args) != 3
                    or args[0] != "$sale_date"
                    or args[1] != 0
                    or args[2] != 7
                    or "sale_date" not in allowed_fields
                ):
                    raise ValueError("Unsupported month grouping expression.")
            elif group_id is not None:
                raise ValueError("Unsupported group identifier.")'''

if old_group not in source:
    if new_group not in source:
        raise SystemExit("ERROR: Could not find the group identifier validator.")
else:
    source = source.replace(old_group, new_group, 1)

# 4. Normalize the question before passing it to query-generation services.
old_endpoint = '''@router.post("/query")
def natural_language_query(request: QueryRequest):
    try:
        aggregation = generate_aggregation_query(request.question)'''

new_endpoint = '''@router.post("/query")
def natural_language_query(request: QueryRequest):
    try:
        normalized_question = normalize_question(request.question)
        aggregation = generate_aggregation_query(normalized_question)'''

if old_endpoint not in source:
    raise SystemExit("ERROR: Could not find the expected query endpoint.")

source = source.replace(old_endpoint, new_endpoint, 1)

# Update only the query-generation/search calls. API responses still return
# the user's original question.
replacements = [
    ("searcher.search(request.question, top_k=3)",
     "searcher.search(normalized_question, top_k=3)"),
    ("generate_query(request.question)",
     "generate_query(normalized_question)"),
    ("generate_llm_query(request.question)",
     "generate_llm_query(normalized_question)"),
]

for old, new in replacements:
    if old not in source:
        raise SystemExit(f"ERROR: Could not find expected code: {old}")
    source = source.replace(old, new, 1)

if source == original:
    raise SystemExit("ERROR: No changes were applied.")

path.write_text(source, encoding="utf-8")
print("SUCCESS: Normalizer connected and validators updated.")
