import { useState, useEffect, useCallback } from "react";

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
  /* ===================== STARTUP ===================== */

  const [showLanding, setShowLanding] = useState(true);
  const [showStartup, setShowStartup] = useState(false);
  const [phase, setPhase] = useState("table");
  const [lastApplyReport, setLastApplyReport] = useState(null);

  /* ===================== FILE DATA ===================== */

  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /* ===================== SELECTION ===================== */

  const [selection, setSelection] = useState({
    entityType: "file",
    entityIds: [],
  });

  /* ===================== SIDE PANEL ===================== */

  const [panelSide] = useState("left");
  const [panelOpen] = useState(true);

  /* ===================== GLOBAL FILTER STATE ===================== */

  const [filters, setFilters] = useState({
    q: "",
    field: "artist",
    starts_with: null,
    genres: new Set(),
  });

  const clearFilters = () => {
    setFilters({
      q: "",
      field: "artist",
      starts_with: null,
      genres: new Set(),
    });
  };

  const onGenresChange = useCallback((updater) => {
    setFilters(prev => {
      const nextGenres =
        typeof updater === "function"
          ? updater(prev.genres)
          : updater;

      return {
        ...prev,
        genres: nextGenres,
      };
    });
  }, []);

  /* ===================== PENDING OPERATIONS ===================== */
  
  const [dirtyFileIds, setDirtyFileIds] = useState([]);
  const [dirtyIds, setDirtyIds] = useState([]);
  const [markedForDeletionIds, setMarkedForDeletionIds] = useState([]);

  const handleDirtyChange = (ids) => {
    setDirtyIds(ids);
  };

  const handleMarkedForDeletionChange = (ids) => {
    setMarkedForDeletionIds(ids);
  };


  /* ===================== FETCH FILES ===================== */

  useEffect(() => {
    const params = new URLSearchParams();

    if (filters.q) {
      params.set("q", filters.q);
      params.set("field", filters.field);
    }

    if (filters.starts_with) {
      params.set("starts_with", filters.starts_with);
      params.set("field", filters.field);
    }

    if (filters.genres.size > 0) {
      params.set("genres", [...filters.genres].join(","));
    }

    if ([...params.keys()].length === 0) {
      setFiles([]);
      return;
    }

    setLoading(true);
    setError(null);

    fetch(`${API_BASE}/files/search?${params.toString()}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setFiles)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [filters]);

  /* ===================== LANDING / STARTUP ===================== */

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

        {/* SIDE PANEL */}
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
              activeGenres={filters.genres}
              onFilterGenres={onGenresChange}
            />
          )}
        </aside>

        {/* MAIN CONTENT */}
        <main className="main-content" style={{ flex: 1, minWidth: 0 }}>
          <FileTable
            files={files}
            loading={loading}
            error={error}

            /* filters */
            filters={filters}
            setFilters={setFilters}
            onClearFilters={clearFilters}

            /* pending ops */
            dirtyIds={dirtyIds}
            markedForDeletionIds={markedForDeletionIds}
            onDirtyChange={handleDirtyChange}
            onMarkedForDeletionChange={handleMarkedForDeletionChange}

            /* navigation */
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
