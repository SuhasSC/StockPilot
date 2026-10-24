from pathlib import Path

path = Path(r"frontend/src/App.jsx")
source = path.read_text(encoding="utf-8")

# Correct the field name to match MongoDB inventory documents.
source = source.replace('"warehouse_location"', '"location"')

# Add analytics prompts without removing existing suggestions.
old = '''  "Find products costing less than 1000",
];'''

new = '''  "Find products costing less than 1000",
  "Show monthly revenue",
  "Show sales by city",
  "How many low stock items",
  "Show category summary",
  "Show best selling products",
  "Show active suppliers",
];'''

if old not in source:
    raise SystemExit(
        "Could not locate the exact suggestions list. No frontend changes saved."
    )

source = source.replace(old, new, 1)
path.write_text(source, encoding="utf-8")
print("SUCCESS: Inventory location field and analytics shortcuts updated.")
