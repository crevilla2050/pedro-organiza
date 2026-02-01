import { useState, useEffect } from "react";
import { t } from "../../i18n";

const API_BASE = "http://127.0.0.1:8000";

export default function ScanStep({ executionPlan, onBack, onDone }) {
  const [status, setStatus] = useState("idle");   // idle | running | success | error
  const [errorKey, setErrorKey] = useState(null);
  const [errorDetails, setErrorDetails] = useState(null);

  // ===== NEW: elapsed time tracking =====
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (status !== "running") return;

    setElapsed(0);
    const start = Date.now();

    const timer = setInterval(() => {
      const seconds = Math.floor((Date.now() - start) / 1000);
      setElapsed(seconds);
    }, 1000);

    return () => clearInterval(timer);
  }, [status]);

  const runScan = async () => {
    setErrorKey(null);
    setErrorDetails(null);
    setStatus("running");

    try {
      const res = await fetch(`${API_BASE}/startup/run-scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan: executionPlan,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      if (data.status !== "ok") {
        setStatus("error");
        setErrorKey(data.error || "STARTUP_SCAN_FAILED");
        setErrorDetails(data.details || null);
        return;
      }

      // ===== DRY-RUN SUCCESS =====
      if (data.mode === "dry-run") {
        setStatus("success");

        setTimeout(() => {
          onDone({
            mode: "dry-run",
            report: data.report,
          });
        }, 600);

        return;
      }

      // ===== REAL SCAN SUCCESS =====
      setStatus("success");

      setTimeout(() => {
        onDone({
          mode: "real",
        });
      }, 600);

    } catch (err) {
      console.error("Scan failed:", err);
      setStatus("error");
      setErrorKey("STARTUP_SCAN_FAILED");
      setErrorDetails(err.message);
    }
  };

  const { database, paths, options } = executionPlan;

  if (!database?.db_path || !paths?.source || !paths?.target) {
    return (
      <div className="startup-step-root">
        <div className="startup-error">
          {t("STARTUP_SCAN_INVALID_PLAN")}
        </div>
      </div>
    );
  }

  // ===== Helper to show evolving running message =====
  const runningMessage = () => {
    if (elapsed < 10) return t("STARTUP_SCAN_RUNNING_HINT");
    if (elapsed < 60) return t("STARTUP_SCAN_RUNNING_LONG") || t("STARTUP_SCAN_RUNNING_HINT");
    if (elapsed < 300) return t("STARTUP_SCAN_RUNNING_VERY_LONG") || t("STARTUP_SCAN_RUNNING_HINT");
    return t("STARTUP_SCAN_RUNNING_HUGE") || t("STARTUP_SCAN_RUNNING_HINT");
  };

  return (
    <div className="startup-step-root">
      <h2>{t("STARTUP_STEP_SCAN")}</h2>

      <p className="startup-hint">
        {t("STARTUP_SCAN_HINT")}
      </p>

      {/* ===== REVIEW SUMMARY ===== */}
      <div className="startup-summary">

        <div className="summary-block">
          <strong>{t("STARTUP_SCAN_DB_LABEL")}</strong>
          <div className="summary-mono">
            {database.db_path}
          </div>
        </div>

        <div className="summary-block">
          <strong>{t("STARTUP_SCAN_SOURCE_LABEL")}</strong>
          <div className="summary-mono">
            {paths.source}
          </div>
        </div>

        <div className="summary-block">
          <strong>{t("STARTUP_SCAN_TARGET_LABEL")}</strong>
          <div className="summary-mono">
            {paths.target}
          </div>
        </div>

        <div className="summary-block">
          <strong>{t("STARTUP_SCAN_MODE_LABEL")}</strong>
          <div>
            {database.mode === "new"
              ? t("STARTUP_SCAN_MODE_NEW")
              : t("STARTUP_SCAN_MODE_EXISTING")}
          </div>
        </div>

        <div className="summary-block">
          <strong>{t("STARTUP_SCAN_OPTIONS_LABEL")}</strong>
          <ul style={{ marginTop: 6 }}>
            <li>
              {t("STARTUP_SCAN_WITH_FINGERPRINT")}:{" "}
              {options?.with_fingerprint ? "✔" : "✖"}
            </li>
            <li>
              {t("STARTUP_SCAN_SEARCH_COVERS")}:{" "}
              {options?.search_covers ? "✔" : "✖"}
            </li>
            <li>
              {t("STARTUP_SCAN_NO_OVERWRITE")}:{" "}
              {options?.no_overwrite ? "✔" : "✖"}
            </li>
            <li>
              {t("STARTUP_SCAN_DRY_RUN")}:{" "}
              {options?.dry_run ? "✔" : "✖"}
            </li>
          </ul>
        </div>
      </div>

      {/* ===== STATUS PANEL ===== */}

      {status === "idle" && (
        <div className="startup-info">
          {t("STARTUP_SCAN_READY")}
        </div>
      )}

      {status === "running" && (
        <div className="startup-info">

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div className="spinner" />
            <strong>{t("STARTUP_SCAN_RUNNING")}</strong>
          </div>

          <div style={{ marginTop: 8 }}>
            {runningMessage()}
          </div>

          <div style={{ marginTop: 8, opacity: 0.8 }}>
            Elapsed time: {Math.floor(elapsed / 60)}:
            {(elapsed % 60).toString().padStart(2, "0")}
          </div>

        </div>
      )}

      {status === "success" && (
        <div className="startup-success">
          {t("STARTUP_SCAN_SUCCESS")}
        </div>
      )}

      {status === "error" && (
        <div className="startup-error">
          <div>{t(errorKey)}</div>
          {errorDetails && (
            <div style={{ marginTop: 6, opacity: 0.8 }}>
              {errorDetails}
            </div>
          )}
        </div>
      )}

      {/* ===== ACTIONS ===== */}
      <div className="startup-actions">

        <button
          className="btn-secondary"
          onClick={onBack}
          disabled={status === "running"}
        >
          {t("BTN_BACK")}
        </button>

        {status === "idle" && (
          <button
            className="btn-primary"
            onClick={runScan}
          >
            {t("STARTUP_BTN_RUN_SCAN")}
          </button>
        )}

        {status === "running" && (
          <button
            className="btn-primary"
            disabled
          >
            {t("STARTUP_SCAN_RUNNING")}
          </button>
        )}

        {status === "error" && (
          <button
            className="btn-primary"
            onClick={runScan}
          >
            {t("STARTUP_BTN_RETRY_SCAN")}
          </button>
        )}
      </div>
    </div>
  );
}
