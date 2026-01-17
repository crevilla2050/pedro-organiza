import { useState } from "react";
import { PlaybackProvider } from "./context/PlaybackContext";
import FileTable from "./components/FileTable";

const EMPTY_FILTERS = {
  q: "",
  field: "artist",      // artist | album | title
  startsWith: null,     // "A".."Z" | "#"
  strict: false,
  caseSensitive: false,
};

export default function App() {
  /* ===================== SIDE PANEL UI STATE ===================== */

  const [panelSide, setPanelSide] = useState("left");
  const [panelOpen, setPanelOpen] = useState(true);

  /* ===================== SEARCH STATE ===================== */

  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  /* ===================== SEARCH ENGINE ===================== */

  const runSearch = async (next = {}) => {
    const f = { ...filters, ...next };
    setFilters(f);

    const isEmpty =
      !f.q &&
      !f.startsWith &&
      !f.strict &&
      !f.caseSensitive;

    // 🚨 CRITICAL RULE:
    // Empty filters = IDLE STATE (NO SEARCH)
    if (isEmpty) {
      setFiles([]);
      setHasSearched(false);
      return;
    }

    setHasSearched(true);
    setLoading(true);

    try {
      const params = new URLSearchParams();

      if (f.q) params.append("q", f.q);
      if (f.field) params.append("field", f.field);
      if (f.startsWith) params.append("starts_with", f.startsWith);
      if (f.strict) params.append("strict", "true");
      if (f.caseSensitive) params.append("case_sensitive", "true");

      const res = await fetch(
        `http://127.0.0.1:8000/files/search?${params.toString()}`
      );

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setFiles(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Search failed:", err);
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS);
    setFiles([]);
    setHasSearched(false);
  };

  /* ===================== RENDER ===================== */

  return (
    <PlaybackProvider>
      <div
        className="app-root"
        style={{
          height: "100%",
          display: "flex",
          flexDirection: panelSide === "left" ? "row" : "row-reverse",
          background: "var(--color-bg-primary)",
          color: "var(--color-text-primary)",
        }}
      >
        {/* ================= SIDE PANEL ================= */}
        <aside
          className={`side-panel ${panelOpen ? "open" : "collapsed"}`}
          style={{
            width: panelOpen ? 260 : 20,
            minWidth: panelOpen ? 260 : 20,
            background: "var(--color-bg-secondary)",
            borderRight:
              panelSide === "left" ? "1px solid var(--color-border)" : "none",
            borderLeft:
              panelSide === "right" ? "1px solid var(--color-border)" : "none",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              padding: panelOpen ? 16 : 6,
              display: "flex",
              justifyContent: "center",
              borderBottom: "1px solid var(--color-divider)",
            }}
          >
            <img
              src="/assets/logo_web.png"
              alt="Pedro Organiza"
              style={{
                width: panelOpen ? 120 : 16,
                transition: "width 0.25s ease",
              }}
            />
          </div>
        </aside>

        {/* ================= MAIN ================= */}
        <div className="main-content" style={{ flex: 1, minWidth: 0 }}>
          <FileTable
            files={files}
            filters={filters}
            loading={loading}
            hasSearched={hasSearched}
            onSearch={runSearch}
            onClear={clearFilters}
          />
        </div>
      </div>
    </PlaybackProvider>
  );
}
