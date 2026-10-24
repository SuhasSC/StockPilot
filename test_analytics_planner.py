from app.services.query_normalizer import normalize_question
from app.services.aggregation_generator import generate_aggregation_query

tests = [
    ("Monthly revenue", "show monthly revenue"),
    ("City-wise sales", "show sales by city"),
    ("Low-stock count", "how many low stock items"),
    ("Category summary", "show category summary"),
    ("Spelling correction", "show monthly revanue"),
    ("Best-selling products", "show best selling products"),
    ("Total completed revenue", "show total revenue"),
    ("Average product price", "show average product price"),
    ("Active suppliers", "show active suppliers"),
]

failed = 0

for label, question in tests:
    try:
        normalized = normalize_question(question)
        plan = generate_aggregation_query(normalized)
        passed = plan is not None
        print(f'{"PASS" if passed else "FAIL"} | {label}')
        print(f"  Input:      {question}")
        print(f"  Normalized: {normalized}")
        if plan:
            print(f"  Collection: {plan.get('collection')}")
            print(f"  Pipeline:   {plan.get('pipeline')}")
        else:
            failed += 1
    except Exception as exc:
        failed += 1
        print(f"FAIL | {label} | {type(exc).__name__}: {exc}")

print(f"\nRESULT: {len(tests) - failed}/{len(tests)} tests passed.")
raise SystemExit(1 if failed else 0)
