from pathlib import Path

path = Path("frontend/src/App.jsx")
text = path.read_text(encoding="utf-8")

text = text.replace(
    'import { useEffect, useMemo, useRef, useState } from "react";',
    'import { useCallback, useEffect, useMemo, useRef, useState } from "react";',
    1,
)

start = text.find("  async function refreshData() {")
end = text.find("\n  const lowStock = inventory.filter(", start)

if start < 0 or end < 0:
    raise SystemExit("Could not locate data loading functions safely.")

replacement = '''  const loadAnalytics = useCallback(async () => {
    setLoadingAnalytics(true);
    const questions = [
      ["revenue", "show total revenue"],
      ["lowStock", "how many low stock items"],
      ["suppliers", "show active suppliers"],
      ["averagePrice", "show average product price"],
      ["completedSales", "show completed sales count"],
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
            completedSales: "completed_sales_count",
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
'''
text = text[:start] + replacement + text[end:]

old_voice = '''  useEffect(() => {
    if (listening && recognitionRef.current) {
      manualStopRef.current = true;
      recognitionRef.current.stop();
      setListening(false);
      setVoiceMessage("Language changed. Press the microphone to start again.");
    }
  }, [voiceLanguage]);'''

new_voice = '''  useEffect(() => {
    if (!listening || !recognitionRef.current) return;

    manualStopRef.current = true;
    recognitionRef.current.stop();
    setListening(false);
    setVoiceMessage("Language changed. Press the microphone to start again.");
  }, [voiceLanguage, listening]);'''

if old_voice not in text:
    raise SystemExit("Could not locate voice-language effect safely.")

text = text.replace(old_voice, new_voice, 1)
path.write_text(text, encoding="utf-8")
print("SUCCESS: Updated React effect and callback dependencies.")
