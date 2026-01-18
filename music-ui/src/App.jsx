import { useState } from "react";
import { PlaybackProvider } from "./context/PlaybackContext";
import FileTable from "./components/FileTable";
import { t } from "./i18n";

const API_BASE = "http://127.0.0.1:8000";

/* ===================== HELPERS ===================== */

function buildSortParam(sortState) {
  // sortState example:
  // [
  //   { field: "artist", dir: "asc", locked: true },
  //   { field: "album", dir: "asc", locked: false }
  // ]

  if (!sortState.length) return null;

  return sortState
    .map(s => `${s.field}:${s.dir}`)
    .join(",");
}

function hasActiveFilters(filters) {
  return Boolean(
    filters.q ||
    filters.starts_with
  );
}

/* ===================== APP ===================== */

export default function App() {
  /* ===== side panel UI ===== */
  const [panelSide, setPanelSide] = useState("left");
  const [panelOpen, setPanelOpen] = useState(true);

  /* ===== search + data ===== */
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /* ===== filters ===== */
  const [filters, setFilters] = useState({
    q: "",
    field: "artist",        // artist | album | title
    starts_with: null,      // A–Z | #
  });

  /* ===== sorting ===== */
  const [sortState, setSortState] = useState([
    { field: "artist", dir: "asc", locked: true },
    { field: "album", dir: "asc", locked: false },
    { field: "title", dir: "asc", locked: false },
  ]);

  /* ===================== SEARCH CORE ===================== */

  const runSearch = async (nextFilters = filters) => {
    if (!hasActiveFilters(nextFilters)) {
      setFiles([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();

      if (nextFilters.q) {
        params.set("q", nextFilters.q);
        params.set("field", nextFilters.field);
      }

      if (nextFilters.starts_with) {
        params.set("field", nextFilters.field);
        params.set("starts_with", nextFilters.starts_with);
      }

      const sortParam = buildSortParam(sortState);
      if (sortParam) {
        params.set("sort", sortParam);
      }

      const res = await fetch(
        `${API_BASE}/files/search?${params.toString()}`
      );

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setFiles(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Search failed:", err);
      setError(t("ERROR_GENERIC"));
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  /* ===================== FILTER ACTIONS ===================== */

  const applyTextSearch = ({ q, field }) => {
    const next = {
      q,
      field,
      starts_with: null,
    };
    setFilters(next);
    runSearch(next);
  };

  const applyAlpha = (letter) => {
    const next = {
      q: "",
      field: filters.field,
      starts_with: letter,
    };
    setFilters(next);
    runSearch(next);
  };

  const clearFilters = () => {
    setFilters({
      q: "",
      field: filters.field,
      starts_with: null,
    });
    setFiles([]);
    setError(null);
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
        }}
      >
        {/* ================= SIDE PANEL ================= */}
        <aside
          className={`side-panel ${panelOpen ? "open" : "collapsed"}`}
          style={{
            width: panelOpen ? 260 : 20,
            minWidth: panelOpen ? 260 : 20,
          }}
        >
          {/* Logo */}
          <div className="side-panel-logo">
            <img
              src="/assets/logo_web.png"
              alt="Pedro Organiza"
              style={{ width: panelOpen ? 120 : 16 }}
            />
          </div>

          {/* Controls */}
          {panelOpen && (
            <div className="side-panel-controls">
              <label>
                <input
                  type="checkbox"
                  checked={panelSide === "right"}
                  onChange={(e) =>
                    setPanelSide(e.target.checked ? "right" : "left")
                  }
                />
                Panel on right
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={panelOpen}
                  onChange={(e) => setPanelOpen(e.target.checked)}
                />
                Panel visible
              </label>
            </div>
          )}

          <div style={{ flex: 1 }} />

          {/* Mini player (mock) */}
          <div className="mini-player">
            <button>⏮</button>
            <button>▶</button>
            <button>⏭</button>
          </div>
        </aside>

        {/* ================= MAIN ================= */}
        <main className="main-content" style={{ flex: 1, minWidth: 0 }}>
          <FileTable
            files={files}
            loading={loading}
            error={error}
            filters={filters}
            setFilters={setFilters}
            onApplySearch={applyTextSearch}
            onAlpha={applyAlpha}
            onClearFilters={clearFilters}
          />
        </main>
      </div>
    </PlaybackProvider>
  );
}
