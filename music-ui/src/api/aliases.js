const API_BASE = "http://127.0.0.1:8000";

export async function fetchAliasClusters({ minSize = 2 } = {}) {
  const res = await fetch(`${API_BASE}/aliases/clusters?min_size=${minSize}`);
  if (!res.ok) {
    throw new Error("Failed to fetch alias clusters");
  }
  return res.json();
}
