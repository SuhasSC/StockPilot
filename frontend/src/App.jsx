import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, AlertTriangle, Bot, Boxes, CheckCircle2, ChevronRight,
  Code2, Database, Languages, LoaderCircle, Mic, MicOff, Package,
  RefreshCw, Search, Send, Sparkles, Warehouse, Volume2, XCircle
} from "lucide-react";
import { getHealth, getProducts, getInventory, runNaturalLanguageQuery } from "./api";
import "./App.css";

const suggestions = [
  "Show products with low stock",
  "Find electronics costing more than 1000",
  "Show all products",
  "Find products costing less than 1000",
  "Show monthly revenue",
  "Show sales by city",
  "How many low stock items",
  "Show category summary",
  "Show best selling products",
  "Show active suppliers",
];

const voiceLanguages = [
  { label: "English (India)", code: "en-IN" },
  { label: "Kannada", code: "kn-IN" },
  { label: "Hindi", code: "hi-IN" },
  { label: "Tamil", code: "ta-IN" },
  { label: "Telugu", code: "te-IN" },
];

const money = (value) => new Intl.NumberFormat("en-IN", {
  style: "currency", currency: "INR", maximumFractionDigits: 0
}).format(Number(value || 0));

function App() {
  const [health, setHealth] = useState(false);
  const [products, setProducts] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [analytics, setAnalytics] = useState({
    revenue: null, lowStock: null, suppliers: null, averagePrice: null,
    completedSales: null
  });
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [question, setQuestion] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("Overview");
  const [showQuery, setShowQuery] = useState(true);

  const [voiceLanguage, setVoiceLanguage] = useState("en-IN");
  const [listening, setListening] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState("");
  const recognitionRef = useRef(null);
  const manualStopRef = useRef(false);

  const loadAnalytics = useCallback(async () => {
    setLoadingAnalytics(true);
    const questions = [
      ["revenue", "show total revenue", "total_revenue"],
      ["lowStock", "how many low stock items", "low_stock_count"],
      ["suppliers", "show active suppliers", "active_supplier_companies"],
      ["averagePrice", "show average product price", "average_price"],
      ["completedSales", "show completed sales count", "completed_sales_count"],
    ];

    const failures = [];
    try {
      await Promise.all(
        questions.map(async ([key, question, field]) => {
          try {
            const result = await runNaturalLanguageQuery(question);
            const first = result.results?.[0] || {};
            if (first[field] === undefined || first[field] === null) {
              throw new Error("API response missing " + field);
            }
            setAnalytics(previous => ({ ...previous, [key]: first[field] }));
          } catch (error) {
            failures.push(question + ": " + error.message);
            console.error("StockPilot analytics query failed:", question, error);
          }
        })
      );

      if (failures.length) {
        setError("Some analytics could not be refreshed. " + failures.join(" | "));
      } else {
        setError("");
      }
    } finally {
      setLoadingAnalytics(false);
    }
  }, []);
  const refreshData = useCallback(async () => {
    setLoadingData(true);
    try {
      const [h, p, i] = await Promise.all([
        getHealth(), getProducts(), getInventory()
      ]);
      setHealth(h.status === "healthy");
      setProducts(p.products || []);
      setInventory(i.inventory || []);
      setError("");
      await loadAnalytics();
    } catch (e) {
      setHealth(false);
      setError(e.message);
    } finally {
      setLoadingData(false);
    }
  }, [loadAnalytics]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshData();
    }, 0);

    return () => {
      window.clearTimeout(timer);
      manualStopRef.current = true;
      recognitionRef.current?.abort();
    };
  }, [refreshData]);

  const lowStock = inventory.filter(
    item => Number(item.stock_quantity) <= Number(item.reorder_level)
  );
  const inventoryValue = useMemo(() => {
    const priceById = Object.fromEntries(
      products.map(p => [p.product_id, Number(p.price || 0)])
    );
    return inventory.reduce((sum, item) =>
      sum + Number(item.stock_quantity || 0) *
        (priceById[item.product_id] || 0), 0);
  }, [products, inventory]);

  async function submitQuery(value = question) {
    const text = value.trim();
    if (text.length < 3) {
      setError("Please enter a question with at least 3 characters.");
      return;
    }
    setQuestion(text);
    setQueryLoading(true);
    setError("");
    setQueryResult(null);
    setActiveTab("AI Query");
    try {
      const result = await runNaturalLanguageQuery(text);
      setQueryResult(result);
      setShowQuery(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setQueryLoading(false);
    }
  }

  function stopVoice() {
    manualStopRef.current = true;
    recognitionRef.current?.stop();
    setListening(false);
    setVoiceMessage("Voice input stopped. You can edit the text and run the query.");
  }

  function startVoice() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceMessage(
        "Speech recognition is not supported in this browser. Try the latest Google Chrome or Microsoft Edge."
      );
      return;
    }

    if (!window.isSecureContext) {
      setVoiceMessage(
        "Microphone access requires localhost or a secure HTTPS connection."
      );
      return;
    }

    recognitionRef.current?.abort();
    manualStopRef.current = false;

    const recognition = new SpeechRecognition();
    recognition.lang = voiceLanguage;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    let finalTranscript = "";

    recognition.onstart = () => {
      setListening(true);
      setVoiceMessage(`Listening in ${voiceLanguages.find(l => l.code === voiceLanguage)?.label}… Speak now.`);
    };

    recognition.onresult = (event) => {
      let interimTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + " ";
        } else {
          interimTranscript += transcript;
        }
      }

      const transcript = (finalTranscript + interimTranscript).trim();
      if (transcript) setQuestion(transcript);
    };

    recognition.onerror = (event) => {
      const messages = {
        "not-allowed": "Microphone permission denied. Allow microphone access in your browser settings.",
        "service-not-allowed": "The browser's speech recognition service is unavailable.",
        "no-speech": "No speech was detected. Try again and speak clearly.",
        "audio-capture": "No microphone was detected. Check your microphone connection.",
        "network": "Speech recognition needs a network connection or its recognition service is unavailable.",
        "language-not-supported": "This browser's recognition service may not support the selected language."
      };
      if (event.error !== "aborted") {
        setVoiceMessage(messages[event.error] || `Voice recognition error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
      if (!manualStopRef.current) {
        setVoiceMessage(previous =>
          previous.startsWith("Listening") || !previous
            ? "Recognition ended. Review the transcription before running your query."
            : previous
        );
      }
    };

    recognitionRef.current = recognition;
    setVoiceMessage("Requesting microphone access…");

    try {
      recognition.start();
    } catch {
      recognitionRef.current = null;
      setListening(false);
      setVoiceMessage("Could not start voice recognition. Please try again.");
    }
  }

  useEffect(() => {
    if (!listening || !recognitionRef.current) return;

    manualStopRef.current = true;
    recognitionRef.current.stop();
    setListening(false);
    setVoiceMessage("Language changed. Press the microphone to start again.");
  }, [voiceLanguage, listening]);

  const resultRows = queryResult?.results || [];
  const columns = resultRows.length
    ? [...new Set(resultRows.flatMap(row => Object.keys(row).filter(k => k !== "_id")))]
    : [];
  if (
    queryResult?.query_type === "aggregate" &&
    resultRows.some(row => Object.prototype.hasOwnProperty.call(row, "_id"))
  ) {
    columns.unshift("_id");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Boxes size={23} /></div>
          <div><strong>StockPilot</strong><span>INTELLIGENT INVENTORY</span></div>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="nav-list">
          {[
            { name: "Overview", icon: Activity },
            { name: "AI Query", icon: Bot },
            { name: "Products", icon: Package },
            { name: "Inventory", icon: Warehouse },
          ].map(({ name, icon: Icon }) => (
            <button key={name}
              className={`nav-item ${activeTab === name ? "active" : ""}`}
              onClick={() => setActiveTab(name)}>
              <Icon size={18} /><span>{name}</span>
              {name === "AI Query" && <span className="nav-ai">AI</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="connection-card">
            <div className="connection-title">
              <span className={`status-dot ${health ? "" : "offline"}`} />
              API CONNECTION
            </div>
            <strong>{health ? "Connected" : "Disconnected"}</strong>
            <span>{health ? "FastAPI is responding" : "Check backend server"}</span>
          </div>
          <div className="sidebar-footer"><Database size={15} /> MongoDB · LLM Engine</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">Workspace <ChevronRight size={14} /> <strong>{activeTab}</strong></div>
          <div className="topbar-right">
            <span className="live-pill"><span className="status-dot" /> SYSTEM LIVE</span>
            <button className="icon-button" onClick={refreshData} title="Refresh data"><RefreshCw size={17} /></button>
            <div className="avatar">AI</div>
          </div>
        </header>

        <div className="page-content">
          <section className="welcome-row">
            <div>
              <div className="eyebrow"><Sparkles size={14} /> AI-POWERED INVENTORY</div>
              <h1>{activeTab === "AI Query" ? "Ask your inventory." : activeTab === "Products" ? "Product catalog." : activeTab === "Inventory" ? "Inventory control." : "Inventory at a glance."}</h1>
              <p>Turn natural language or voice into actionable inventory insights.</p>
            </div>
            <button className="secondary-button" onClick={refreshData} disabled={loadingData}>
              <RefreshCw size={15} className={loadingData ? "spin" : ""} /> Refresh data
            </button>
          </section>

          {error && <div className="error-banner"><XCircle size={18} /><span>{error}</span><button onClick={() => setError("")}><XCircle size={16} /></button></div>}

          <section className="query-card">
            <div className="query-card-top">
              <div className="ai-icon"><Bot size={21} /></div>
              <div className="query-title"><strong>Ask your inventory</strong><span>Natural language · MongoDB query generation</span></div>
              <span className="powered-pill"><Sparkles size={12} /> AI POWERED</span>
            </div>

            <div className="voice-controls">
              <label htmlFor="voice-language"><Languages size={16} /> Spoken language</label>
              <select id="voice-language" value={voiceLanguage}
                onChange={e => setVoiceLanguage(e.target.value)}
                disabled={listening}>
                {voiceLanguages.map(language => (
                  <option key={language.code} value={language.code}>{language.label}</option>
                ))}
              </select>
              <button type="button"
                className={`mic-button ${listening ? "recording" : ""}`}
                onClick={listening ? stopVoice : startVoice}
                aria-pressed={listening}>
                {listening ? <MicOff size={17} /> : <Mic size={17} />}
                {listening ? "Stop listening" : "Speak question"}
              </button>
              {listening && <span className="recording-indicator"><span /> Listening</span>}
            </div>

            <div className={`voice-message ${voiceMessage.startsWith("Microphone permission denied") || voiceMessage.startsWith("Speech recognition is not supported") || voiceMessage.startsWith("Could not") ? "voice-error" : ""}`} aria-live="polite">
              {voiceMessage && <><Volume2 size={14} /><span>{voiceMessage}</span></>}
            </div>

            <form className="query-form" onSubmit={e => { e.preventDefault(); submitQuery(); }}>
              <Search size={19} className="query-search-icon" />
              <input value={question} onChange={e => setQuestion(e.target.value)}
                placeholder="Type or speak a question in your selected language…"
                maxLength={500} aria-label="Ask your inventory" />
              <button className="run-button" type="submit" disabled={queryLoading}>
                {queryLoading ? <LoaderCircle className="spin" size={17} /> : <Send size={16} />}
                {queryLoading ? "Running..." : "Run query"}
              </button>
            </form>

            <div className="suggestion-row"><span>TRY ASKING</span>
              {suggestions.map(s => <button key={s} onClick={() => { setQuestion(s); submitQuery(s); }}>{s}</button>)}
            </div>
          </section>

          {activeTab === "Overview" && (
            <section className="stats-grid">
              <StatCard icon={Package} label="TOTAL PRODUCTS" value={loadingData ? "—" : products.length} note="Products in catalog" tone="blue" />
              <StatCard icon={AlertTriangle} label="LOW STOCK ITEMS" value={loadingData ? "—" : lowStock.length} note="At or below reorder level" tone="amber" />
              <StatCard icon={Boxes} label="UNITS IN STOCK" value={loadingData ? "—" : inventory.reduce((s, x) => s + Number(x.stock_quantity || 0), 0)} note="Across tracked inventory" tone="violet" />
              <StatCard icon={Database} label="STOCK VALUE" value={loadingData ? "—" : money(inventoryValue)} note="Estimated using product prices" tone="green" />
            </section>
          )}

          {activeTab === "Overview" && (
            <section className="stats-grid analytics-kpi-grid">
              <StatCard icon={Activity} label="COMPLETED REVENUE"
                value={loadingAnalytics || analytics.revenue === null ? "—" : money(analytics.revenue)}
                note="Completed sales only" tone="green" />
              <StatCard icon={Activity} label="COMPLETED SALES"
                value={loadingAnalytics || analytics.completedSales === null ? "—" : analytics.completedSales}
                note="Completed sales records" tone="amber" />
              <StatCard icon={Warehouse} label="ACTIVE SUPPLIERS"
                value={loadingAnalytics || analytics.suppliers === null ? "—" : analytics.suppliers}
                note="Distinct supplier companies" tone="violet" />
              <StatCard icon={Boxes} label="AVERAGE PRODUCT PRICE"
                value={loadingAnalytics || analytics.averagePrice === null ? "—" : money(analytics.averagePrice)}
                note="Average across product catalog" tone="blue" />
            </section>
          )}

          {queryResult && (
            <section className="panel result-panel">
              <div className="panel-header">
                <div><div className="panel-kicker"><CheckCircle2 size={14} /> QUERY COMPLETED</div>
                  <h2>Query results <span className="count-pill">{queryResult.count} records</span></h2>
                  <p>{queryResult.description || "Results returned from your inventory database."}</p></div>
                <button className="secondary-button small" onClick={() => setShowQuery(v => !v)}><Code2 size={15} /> {showQuery ? "Hide query" : "Show query"}</button>
              </div>
              {showQuery && <div className="generated-query">
                <div className="code-heading"><Code2 size={14} /> GENERATED MONGODB FILTER <span>{queryResult.generation_method || "unknown method"}</span></div>
                <pre>{JSON.stringify(queryResult.generated_query || {}, null, 2)}</pre>
                <div className="collection-label">Collection: <strong>{queryResult.collection}</strong></div>
              </div>}
              {resultRows.length ? (
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
                  {queryResult.collection === "products" &&
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
                  <div className="table-wrap"><table>
                    <thead><tr>{columns.map(c => (
                      <th key={c}>{c === "_id" ? (
                        resultRows.some(row => /^\d{4}-\d{2}$/.test(String(row._id))) ? "Month"
                        : queryResult.collection === "products" ? "Category"
                        : queryResult.collection === "sales" && resultRows.some(row => typeof row._id === "string" && !/^P\d+/.test(row._id)) ? "City"
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
              ) : <div className="empty-state"><Search size={24} /><strong>No matching records</strong><span>The query completed but returned no records.</span></div>}
              {queryResult.similar_examples?.length > 0 && <div className="similar-examples"><strong><Languages size={15} /> Similar examples used for context</strong>
                {queryResult.similar_examples.slice(0, 3).map((ex, i) => <span key={i}>{ex.question} <small>{(Number(ex.similarity || 0) * 100).toFixed(0)}%</small></span>)}
              </div>}
            </section>
          )}

          {(activeTab === "Overview" || activeTab === "Products" || activeTab === "Inventory") && (
            <section className="panel">
              <div className="panel-header">
                <div><div className="panel-kicker"><Database size={14} /> LIVE MONGODB DATA</div>
                  <h2>{activeTab === "Inventory" ? "Inventory levels" : activeTab === "Products" ? "Product catalog" : "Recent products"}</h2>
                  <p>{activeTab === "Inventory" ? "Current stock levels and reorder thresholds." : "Loaded directly from your FastAPI backend."}</p></div>
                <span className="count-pill">{activeTab === "Inventory" ? inventory.length : products.length} records</span>
              </div>
              {activeTab === "Inventory" ? <DataTable rows={inventory} inventory /> : <DataTable rows={products} />}
            </section>
          )}

          <footer className="page-footer"><span>StockPilot <span className="footer-dot">•</span> LLM NoSQL Inventory Management</span>
            <span><span className={`status-dot ${health ? "" : "offline"}`} /> {health ? "API connected" : "API offline"} <span className="footer-dot">·</span> React + FastAPI + MongoDB</span></footer>
        </div>
      </main>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, note, tone }) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={19} /></div>
    <div className="stat-label">{label}</div><div className="stat-value">{value}</div>
    <div className="stat-note">{note}</div></div>;
}

function DataTable({ rows, inventory = false }) {
  if (!rows?.length) return <div className="empty-state"><Package size={24} /><strong>No records available</strong><span>Check that MongoDB has data.</span></div>;
  const fields = inventory
    ? ["product_id", "stock_quantity", "reorder_level", "location"]
    : ["product_id", "name", "category", "price", "supplier_id"];
  return <div className="table-wrap"><table><thead><tr>{fields.map(f => <th key={f}>{f.replaceAll("_", " ")}</th>)}</tr></thead>
    <tbody>{rows.map((row, i) => <tr key={row.product_id || i}>{fields.map(f => <td key={f}>
      {f === "price" ? money(row[f]) : f === "stock_quantity" && Number(row[f]) <= Number(row.reorder_level)
        ? <span className="stock-warning"><AlertTriangle size={13} /> {row[f]} units</span>
        : f === "category" ? <span className="category-chip">{row[f]}</span> : String(row[f] ?? "—")}
    </td>)}</tr>)}</tbody></table></div>;
}

export default App;





