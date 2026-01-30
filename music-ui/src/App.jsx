import { useState, useEffect } from "react";
import { PlaybackProvider } from "./context/PlaybackContext";

import LandingPage from "./LandingPage";
import StartupPage from "./startup/StartupPage";
import ApplyStep from "./startup/steps/ApplyStep";
import DoneStep from "./startup/steps/DoneStep";
import FileTable from "./components/FileTable";

import { t } from "./i18n";
import pedroLogo from "./assets/logo.png";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  /* ===================== STARTUP GATE ===================== */

  const [showLanding, setShowLanding] = useState(true);
  const [showStartup, setShowStartup] = useState(false);

  /* ===================== MAIN WORKFLOW ===================== */

  const [phase, setPhase] = useState("table"); // "table" | "apply" | "done"
  const [lastApplyReport, setLastApplyReport] = useState(null);

  /* ===================== FILE TABLE STATE ===================== */

  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /* ===================== SIDE PANEL UI ===================== */

  const [panelSide, setPanelSide] = useState("left");
  const [panelOpen, setPanelOpen] = useState(true);

  /* ===================== INITIAL LOAD ===================== */

  useEffect(() => {
    // Load initial file list once we enter main UI
    if (!showLanding && !showStartup) {
      loadInitialFiles();
    }
  }, [showLanding, showStartup]);

  const loadInitialFiles = async () => {
    // Initial state: do NOT load any files.
    // Files will only be loaded when the user applies a filter.

    setFiles([]);
    setLoading(false);
    setError(null);
  };


  /* ===================== SEARCH / ALPHA WIRING ===================== */

  const applySearch = async (q, field) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `${API_BASE}/files/search?q=${encodeURIComponent(q)}&field=${field}`
      );

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setFiles(data);
    } catch (e) {
      console.error("Search failed:", e);
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const applyAlpha = async (letter, field) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `${API_BASE}/files/search?starts_with=${encodeURIComponent(letter)}&field=${field}`
      );

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setFiles(data);
    } catch (e) {
      console.error("Alpha search failed:", e);
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  /* ===================== LANDING PAGE ===================== */

  if (showLanding) {
    return (
      <LandingPage
        onEnterWizard={() => {
          setShowLanding(false);
          setShowStartup(true);
        }}
        onEnterDirect={() => {
          setShowLanding(false);
          setShowStartup(false);
        }}
      />
    );
  }

  /* ===================== STARTUP WIZARD ===================== */

  if (showStartup) {
    return (
      <StartupPage
        onComplete={() => {
          setShowStartup(false);
        }}
      />
    );
  }

  /* ===================== APPLY PHASE ===================== */

  if (phase === "apply") {
    return (
      <ApplyStep
        onDone={(report) => {
          setLastApplyReport(report);
          setPhase("done");
        }}
        onCancel={() => setPhase("table")}
      />
    );
  }

  if (phase === "done") {
    return (
      <DoneStep
        report={lastApplyReport}
        onBackToTable={() => setPhase("table")}
      />
    );
  }

  /* ===================== MAIN UI ===================== */

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
        {/* ===================== SIDE PANEL ===================== */}
        <aside
          className={`side-panel ${panelOpen ? "open" : "collapsed"}`}
          style={{
            width: panelOpen ? 260 : 20,
            minWidth: panelOpen ? 260 : 20,
          }}
        >
          <div className="side-panel-logo">
            <img
              src={pedroLogo}
              alt={t("APP_NAME")}
              style={{ width: panelOpen ? 120 : 16 }}
            />
          </div>

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

          <div className="mini-player">
            <button>⏮</button>
            <button>▶</button>
            <button>⏭</button>
          </div>
        </aside>

        {/* ===================== MAIN CONTENT ===================== */}
        <main className="main-content" style={{ flex: 1, minWidth: 0 }}>
          <FileTable
            files={files}
            loading={loading}
            error={error}
            onApplySearch={applySearch}
            onAlpha={applyAlpha}
            onGoToApply={() => setPhase("apply")}
            onUpdateFile={(id, patch) => {
              setFiles(prev =>
                prev.map(row =>
                  row.id === id ? { ...row, ...patch } : row
                )
              );
            }}
          />
        </main>
      </div>
    </PlaybackProvider>
  );
}
