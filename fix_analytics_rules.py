from pathlib import Path

path = Path(r"backend/app/services/aggregation_generator.py")
source = path.read_text(encoding="utf-8")

old_best = '''        "sold the most", "best-selling", "bestselling",
        "top selling", "top-selling", "highest selling",
        "most units sold",'''

new_best = '''        "sold the most", "best-selling", "best selling", "bestselling",
        "top selling", "top-selling", "highest selling",
        "most units sold",'''

old_supplier = '''    if (
        "supplier" in text
        and any(term in text for term in [
            "how many", "count", "number of", "total",
        ])
        and "active" in text
    ):'''

new_supplier = '''    if (
        "supplier" in text
        and "active" in text
        and (
            any(term in text for term in [
                "how many", "count", "number of", "total",
            ])
            or any(term in text for term in [
                "show active suppliers", "list active suppliers",
                "active supplier companies",
            ])
        )
    ):'''

if old_best not in source:
    raise SystemExit("ERROR: Best-selling rule text not found; no changes saved.")

if old_supplier not in source:
    raise SystemExit("ERROR: Active-supplier rule text not found; no changes saved.")

source = source.replace(old_best, new_best, 1)
source = source.replace(old_supplier, new_supplier, 1)
path.write_text(source, encoding="utf-8")

print("SUCCESS: Both planner rules updated.")
