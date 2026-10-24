const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `API request failed (${response.status})`);
  }
  return data;
}

export const getHealth = () => request("/api/health");
export const getProducts = () => request("/api/products");
export const getInventory = () => request("/api/inventory");

export const runNaturalLanguageQuery = (question) =>
  request("/api/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
