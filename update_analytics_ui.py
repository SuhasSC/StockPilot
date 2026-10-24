from pathlib import Path

app_path = Path(r"frontend/src/App.jsx")
css_path = Path(r"frontend/src/App.css")

source = app_path.read_text(encoding="utf-8")
css = css_path.read_text(encoding="utf-8")

old_columns = '''  const resultRows = queryResult?.results || [];
  const columns = resultRows.length
    ? [...new Set(resultRows.flatMap(row =>
        Object.keys(row).filter(k => k !== "_id")))]
    : [];'''

new_columns = '''  const resultRows = queryResult?.results || [];
  const columns = resultRows.length
    ? [...new Set(resultRows.flatMap(row => Object.keys(row).filter(k => k !== "_id")))]
    : [];
  if (
    queryResult?.query_type === "aggregate" &&
    resultRows.some(row => Object.prototype.hasOwnProperty.call(row, "_id"))
  ) {
    columns.unshift("_id");
  }'''

if old_columns not in source:
    raise SystemExit("Could not find the exact resultRows/columns block.")

old_table = '''              {resultRows.length ? (
                <div className="table-wrap"><table><thead><tr>{columns.map(c => <th key={c}>{c.replaceAll("_", " ")}</th>)}</tr></thead>
                  <tbody>{resultRows.map((row, i) => <tr key={row.product_id || i}>{columns.map(c => <td key={c}>{typeof row[c] === "object" ? JSON.stringify(row[c]) : String(row[c] ?? "—")}</td>)}</tr>)}</tbody>
                </table></div>
              ) : <div className="empty-state"><Search size={24} /><strong>No matching records</strong><span>The query completed but returned no records.</span></div>}'''

new_table = '''              {resultRows.length ? (
                <>
                  {queryResult.query_type === "aggregate" &&
                    resultRows.some(row => Number.isFinite(Number(row.total_revenue))) && (
                    <div className="analytics-chart">
                      <div className="analytics-chart-title">
                        <strong>Revenue overview</strong>
                        <span>Completed sales · INR</span>
                      </div>
                      {resultRows.map((row, i) => {
                        const amount = Number(row.total_revenue || 0);
                        const max = Math.max(...resultRows.map(item => Number(item.total_revenue || 0)), 1);
                        return (
                          <div className="revenue-bar-row" key={`${row._id ?? "total"}-${i}`}>
                            <span className="revenue-bar-label">{row._id ?? "Total"}</span>
                            <div className="revenue-bar-track">
                              <div className="revenue-bar-fill" style={{ width: `${Math.max(1, amount / max * 100)}%` }} />
                            </div>
                            <strong>{money(amount)}</strong>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  <div className="table-wrap"><table>
                    <thead><tr>{columns.map(c => (
                      <th key={c}>{c === "_id" ? (
                        resultRows.some(row => /^\\d{4}-\\d{2}$/.test(String(row._id))) ? "Month"
                        : queryResult.collection === "products" ? "Category"
                        : queryResult.collection === "sales" && resultRows.some(row => typeof row._id === "string" && !/^P\\d+/.test(row._id)) ? "City"
                        : "Group / ID"
                      ) : c.replaceAll("_", " ")}</th>
                    ))}</tr></thead>
                    <tbody>{resultRows.map((row, i) => (
                      <tr key={row.product_id || row._id || i}>{columns.map(c => {
                        const value = row[c];
                        const moneyFields = ["total_revenue", "average_price", "price", "unit_price", "total_amount"];
                        return <td key={c}>{value == null ? "—"
                          : moneyFields.includes(c) && Number.isFinite(Number(value)) ? money(value)
                          : typeof value === "object" ? JSON.stringify(value)
                          : String(value)}</td>;
                      })}</tr>
                    ))}</tbody>
                  </table></div>
                </>
              ) : <div className="empty-state"><Search size={24} /><strong>No matching records</strong><span>The query completed but returned no records.</span></div>}'''

if old_table not in source:
    raise SystemExit("Could not find the exact query results table.")

source = source.replace(old_columns, new_columns, 1)
source = source.replace(old_table, new_table, 1)

css_addition = '''

/* StockPilot analytics chart */
.analytics-chart {
  margin: 22px 0;
  padding: 20px;
  border: 1px solid #263244;
  border-radius: 14px;
  background: rgba(20, 27, 39, 0.7);
}
.analytics-chart-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}
.analytics-chart-title strong { color: #e8edf7; }
.analytics-chart-title span { color: #8ea3c3; font-size: 12px; }
.revenue-bar-row {
  display: grid;
  grid-template-columns: minmax(65px, 95px) minmax(50px, 1fr) minmax(90px, 125px);
  gap: 12px;
  align-items: center;
  margin: 12px 0;
  font-size: 12px;
}
.revenue-bar-label { color: #a9bad5; overflow-wrap: anywhere; }
.revenue-bar-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #252e40;
}
.revenue-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #6c63ff, #a78bfa);
}
.revenue-bar-row strong {
  text-align: right;
  color: #e5eaff;
  font-variant-numeric: tabular-nums;
}
@media (max-width: 640px) {
  .revenue-bar-row { grid-template-columns: 58px minmax(30px, 1fr) 88px; gap: 7px; }
  .revenue-bar-row strong { font-size: 11px; }
}
'''

if "/* StockPilot analytics chart */" not in css:
    css += css_addition

app_path.write_text(source, encoding="utf-8")
css_path.write_text(css, encoding="utf-8")
print("SUCCESS: Group column, INR formatting, and revenue chart added.")
