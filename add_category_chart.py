from pathlib import Path

app_path = Path("frontend/src/App.jsx")
css_path = Path("frontend/src/App.css")

source = app_path.read_text(encoding="utf-8")
css = css_path.read_text(encoding="utf-8")

anchor = '''                  <div className="table-wrap"><table>
                    <thead><tr>{columns.map(c => ('''

category_chart = '''                  {queryResult.collection === "products" &&
                    resultRows.some(row => Number.isFinite(Number(row.product_count)) &&
                      Number.isFinite(Number(row.average_price))) && (
                    <div className="analytics-chart category-chart">
                      <div className="analytics-chart-title">
                        <strong>Category overview</strong>
                        <span>Product count · Average price in INR</span>
                      </div>
                      {(() => {
                        const maxCount = Math.max(
                          ...resultRows.map(row => Number(row.product_count || 0)), 1
                        );
                        return resultRows.map((row, i) => (
                          <div className="category-chart-row" key={`${row._id}-${i}`}>
                            <div className="category-chart-heading">
                              <strong>{String(row._id ?? "Uncategorized")}</strong>
                              <span>{Number(row.product_count || 0)} products</span>
                            </div>
                            <div className="revenue-bar-track">
                              <div className="revenue-bar-fill"
                                style={{ width: `${Math.max(1, Number(row.product_count || 0) / maxCount * 100)}%` }} />
                            </div>
                            <div className="category-chart-price">
                              Average price <strong>{money(row.average_price)}</strong>
                            </div>
                          </div>
                        ));
                      })()}
                    </div>
                  )}
'''

if "Category overview" not in source:
    if anchor not in source:
        raise SystemExit("Could not locate the results table insertion point; no changes made.")
    source = source.replace(anchor, category_chart + anchor, 1)

css_addition = '''
.category-chart-row {
  margin: 17px 0 21px;
}
.category-chart-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 9px;
  color: #a9bad5;
  font-size: 12px;
}
.category-chart-heading strong { color: #e8edf7; }
.category-chart-price {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
  color: #8ea3c3;
  font-size: 12px;
}
.category-chart-price strong {
  color: #e5eaff;
  font-variant-numeric: tabular-nums;
}
'''

if ".category-chart-row" not in css:
    css += "\n" + css_addition

app_path.write_text(source, encoding="utf-8")
css_path.write_text(css, encoding="utf-8")
print("SUCCESS: Category visualization added.")
