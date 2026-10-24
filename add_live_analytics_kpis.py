from pathlib import Path

app_path = Path(r"frontend/src/App.jsx")
css_path = Path(r"frontend/src/App.css")
source = app_path.read_text(encoding="utf-8")
css = css_path.read_text(encoding="utf-8")

old_state = '''  const [inventory, setInventory] = useState([]);
  const [loadingData, setLoadingData] = useState(true);'''

new_state = '''  const [inventory, setInventory] = useState([]);
  const [analytics, setAnalytics] = useState({
    revenue: null, lowStock: null, suppliers: null, averagePrice: null
  });
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [loadingData, setLoadingData] = useState(true);'''

old_refresh = '''      const [h, p, i] = await Promise.all([
        getHealth(), getProducts(), getInventory()
      ]);
      setHealth(h.status === "healthy");
      setProducts(p.products || []);
      setInventory(i.inventory || []);
      setError("");'''

new_refresh = '''      const [h, p, i] = await Promise.all([
        getHealth(), getProducts(), getInventory()
      ]);
      setHealth(h.status === "healthy");
      setProducts(p.products || []);
      setInventory(i.inventory || []);
      setError("");
      loadAnalytics();'''

if old_state not in source:
    raise SystemExit("Could not find the expected React state block.")
if old_refresh not in source:
    raise SystemExit("Could not find the expected refreshData block.")

source = source.replace(old_state, new_state, 1)
source = source.replace(old_refresh, new_refresh, 1)

marker = '''  useEffect(() => {
    refreshData();'''

analytics_function = '''  async function loadAnalytics() {
    setLoadingAnalytics(true);
    const questions = [
      ["revenue", "show total revenue"],
      ["lowStock", "how many low stock items"],
      ["suppliers", "show active suppliers"],
      ["averagePrice", "show average product price"],
    ];

    try {
      const entries = await Promise.all(
        questions.map(async ([key, question]) => {
          const result = await runNaturalLanguageQuery(question);
          const first = result.results?.[0] || {};
          const field = {
            revenue: "total_revenue",
            lowStock: "low_stock_count",
            suppliers: "active_supplier_companies",
            averagePrice: "average_price",
          }[key];
          return [key, first[field] ?? null];
        })
      );
      setAnalytics(previous => ({ ...previous, ...Object.fromEntries(entries) }));
    } catch (error) {
      console.error("Could not load StockPilot analytics:", error);
    } finally {
      setLoadingAnalytics(false);
    }
  }

'''

if marker not in source:
    raise SystemExit("Could not locate the initial useEffect block.")

source = source.replace(marker, analytics_function + marker, 1)

old_stats_end = '''              <StatCard icon={Database} label="STOCK VALUE" value={loadingData ? "—" : money(inventoryValue)} note="Estimated using product prices" tone="green" />
            </section>'''

new_stats_end = '''              <StatCard icon={Database} label="STOCK VALUE" value={loadingData ? "—" : money(inventoryValue)} note="Estimated using product prices" tone="green" />
            </section>
          )}

          {activeTab === "Overview" && (
            <section className="stats-grid analytics-kpi-grid">
              <StatCard icon={Activity} label="COMPLETED REVENUE"
                value={loadingAnalytics || analytics.revenue === null ? "—" : money(analytics.revenue)}
                note="Completed sales only" tone="green" />
              <StatCard icon={AlertTriangle} label="LOW STOCK (API)"
                value={loadingAnalytics || analytics.lowStock === null ? "—" : analytics.lowStock}
                note="At or below reorder level" tone="amber" />
              <StatCard icon={Warehouse} label="ACTIVE SUPPLIERS"
                value={loadingAnalytics || analytics.suppliers === null ? "—" : analytics.suppliers}
                note="Distinct supplier companies" tone="violet" />
              <StatCard icon={Boxes} label="AVERAGE PRODUCT PRICE"
                value={loadingAnalytics || analytics.averagePrice === null ? "—" : money(analytics.averagePrice)}
                note="Average across product catalog" tone="blue" />
            </section>'''

if old_stats_end not in source:
    raise SystemExit("Could not locate the overview inventory cards.")

source = source.replace(old_stats_end, new_stats_end, 1)

css_addition = '''
.analytics-kpi-grid { margin-top: 18px; }
'''

if ".analytics-kpi-grid" not in css:
    css += "\\n" + css_addition

app_path.write_text(source, encoding="utf-8")
css_path.write_text(css, encoding="utf-8")
print("SUCCESS: Live analytics KPI cards added.")
