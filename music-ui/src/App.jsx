import { useState, useEffect } from "react";
import { PlaybackProvider } from "./context/PlaybackContext";

import LandingPage from "./LandingPage";
import StartupPage from "./startup/StartupPage";
import ApplyStep from "./startup/steps/ApplyStep";
import DoneStep from "./startup/steps/DoneStep";
import FileTable from "./components/FileTable";
import GenresPanel from "./components/GenresPanel";

import { t } from "./i18n";
import pedroLogo from "./assets/logo.png";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  /* ===================== STARTUP GATE ===================== */

  const [showLanding, setShowLanding] = useState(true);
  const [showStartup, setShowStartup] = useState(false);

  /* ===================== MAIN WORKFLOW ===================== */

  const [phase, setPhase] = useState("table");
  const [lastApplyReport, setLastApplyReport] = useState(null);

  /* ===================== FILE TABLE STATE ===================== */

  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /* ===================== SIDE PANEL ===================== */

  const [panelSide, setPanelSide] = useState("left");
  const [panelOpen, setPanelOpen] = useState(true);

  /* ===================== SELECTION ===================== */

  const [selection, setSelection] = useState({
    entityType: "file",
    entityIds: [],
  });

  /* ===================== GENRE FILTER STATE ===================== */

  const [activeGenres, _setActiveGenres] = useState(new Set());

  const setActiveGenres = (updater) => {
    _setActiveGenres(prev => {
      if (updater instanceof Set) return updater;
      if (typeof updater === "function") {
        const next = updater(prev);
        return next instanceof Set ? next : prev;
      }
      return prev; // ignore invalid writes
    });
  };

  const [genreQuery, setGenreQuery] = useState("");  
  const [filterMode, setFilterMode] = useState(true); // true = no file selection

  /* ---------- switch filter/edit mode ---------- */
  useEffect(() => {
    setFilterMode(selection.entityIds.length === 0);
  }, [selection]);

  /* ===================== INITIAL LOAD ===================== */

  useEffect(() => {
    if (!showLanding && !showStartup) {
      setFiles([]);
      setLoading(false);
      setError(null);
    }
  }, [showLanding, showStartup]);


  /* ===================== FILE TABLE ACTIONS ===================== */  
  useEffect(() => {
    if (activeGenres.size === 0) return;

    const genresParam = Array.from(activeGenres).join(",");

    setLoading(true);
    setError(null);

    fetch(
      `${API_BASE}/files/search?genres=${encodeURIComponent(genresParam)}`
    )
      .then(res => res.json())
      .then(setFiles)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [activeGenres]);


  /* ===================== SEARCH / ALPHA ===================== */

  const buildGenreParam = () =>
    activeGenres.size
      ? `&genres=${encodeURIComponent([...activeGenres].join(","))}`
      : "";

  const applySearch = async (q, field) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `${API_BASE}/files/search?q=${encodeURIComponent(q)}&field=${field}${buildGenreParam()}`
      );

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setFiles(await res.json());
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
        `${API_BASE}/files/search?starts_with=${encodeURIComponent(letter)}&field=${field}${buildGenreParam()}`
      );

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setFiles(await res.json());
    } catch (e) {
      console.error("Alpha search failed:", e);
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  /* ===================== LANDING ===================== */

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

  if (showStartup) {
    return <StartupPage onComplete={() => setShowStartup(false)} />;
  }

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
          style={{ width: panelOpen ? 260 : 20 }}
        >
          <div className="side-panel-logo">
            <img
              src={pedroLogo}
              alt={t("APP_NAME")}
              style={{ width: panelOpen ? 120 : 16 }}
            />
          </div>

          {panelOpen && (
            <GenresPanel
              selection={selection}
              activeGenres={activeGenres}
              onFilterGenres={setActiveGenres}
            />
          )}
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
            onSelectionChange={setSelection}
            onUpdateFile={(id, patch) => {
              setFiles((prev) =>
                prev.map((row) =>
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
