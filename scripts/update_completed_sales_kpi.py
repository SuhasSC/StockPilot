from pathlib import Path

planner_path = Path("backend/app/services/aggregation_generator.py")
app_path = Path("frontend/src/App.jsx")

planner = planner_path.read_text(encoding="utf-8")
app = app_path.read_text(encoding="utf-8")

# Add a completed-sales count aggregation rule.
anchor = "    # Average product price."
new_rule = '''    # Count completed sales records.
    if any(term in text for term in [
        "completed sales count", "count completed sales",
        "number of completed sales", "how many completed sales",
    ]):
        return {
            "query_type": "aggregate",
            "collection": "sales",
            "pipeline": [
                {"$match": {"status": "completed"}},
                {"$group": {"_id": None, "completed_sales_count": {"$sum": 1}}},
            ],
            "description": "Count completed sales records",
        }

'''
if "completed_sales_count" not in planner:
    if anchor not in planner:
        raise SystemExit("Could not locate planner insertion point.")
    planner = planner.replace(anchor, new_rule + anchor, 1)

# Add the KPI question to the existing analytics loader.
old_questions = '''      ["averagePrice", "show average product price"],
    ];'''
new_questions = '''      ["averagePrice", "show average product price"],
      ["completedSales", "show completed sales count"],
    ];'''
if old_questions not in app:
    raise SystemExit("Could not find analytics question list.")
app = app.replace(old_questions, new_questions, 1)

old_fields = '''            averagePrice: "average_price",
          }[key];'''
new_fields = '''            averagePrice: "average_price",
            completedSales: "completed_sales_count",
          }[key];'''
if old_fields not in app:
    raise SystemExit("Could not find analytics field mapping.")
app = app.replace(old_fields, new_fields, 1)

old_card = '''              <StatCard icon={AlertTriangle} label="LOW STOCK (API)"
                value={loadingAnalytics || analytics.lowStock === null ? "—" : analytics.lowStock}
                note="At or below reorder level" tone="amber" />'''
new_card = '''              <StatCard icon={Activity} label="COMPLETED SALES"
                value={loadingAnalytics || analytics.completedSales === null ? "—" : analytics.completedSales}
                note="Completed sales records" tone="amber" />'''
if old_card not in app:
    raise SystemExit("Could not find duplicate Low Stock KPI card.")
app = app.replace(old_card, new_card, 1)

# Add state for the new KPI.
old_state = '''    revenue: null, lowStock: null, suppliers: null, averagePrice: null
  });'''
new_state = '''    revenue: null, lowStock: null, suppliers: null, averagePrice: null,
    completedSales: null
  });'''
if old_state not in app:
    raise SystemExit("Could not find analytics state.")
app = app.replace(old_state, new_state, 1)

planner_path.write_text(planner, encoding="utf-8")
app_path.write_text(app, encoding="utf-8")
print("SUCCESS: Completed Sales KPI added; duplicate low-stock card removed.")
