import { t } from "../../i18n";

/* ===== Helpers to export files ===== */

function downloadText(filename, text) {
  const blob = new Blob([text], { type: "application/octet-stream" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();

  URL.revokeObjectURL(url);
}

function toXML(obj, indent = "") {
  if (obj === null || obj === undefined) {
    return `${indent}<null />\n`;
  }

  if (typeof obj !== "object") {
    return `${indent}${String(obj)}\n`;
  }

  let xml = "";

  for (const key of Object.keys(obj)) {
    const value = obj[key];

    if (typeof value === "object" && value !== null) {
      xml += `${indent}<${key}>\n`;
      xml += toXML(value, indent + "  ");
      xml += `${indent}</${key}>\n`;
    } else {
      xml += `${indent}<${key}>${String(value)}</${key}>\n`;
    }
  }

  return xml;
}

export default function DoneStep({
  executionPlan,      // Startup mode
  report,             // Apply mode
  onRestartWizard,   // Startup mode
  onEnterPedro,      // Startup mode
  onBackToTable,     // Apply mode
}) {
  const isApplyMode = !!report;

  /* ===== Build summary for Startup mode ===== */

  let summary = null;

  if (!isApplyMode && executionPlan) {
    const { database, paths, options, layout, review } = executionPlan;

    summary = {
      finished_at: new Date().toISOString(),
      database,
      paths,
      options,
      layout,
      review,
    };
  }

  const handleDownloadJSON = () => {
    if (!summary) return;
    const text = JSON.stringify(summary, null, 2);
    downloadText("pedro_last_run.json", text);
  };

  const handleDownloadXML = () => {
    if (!summary) return;

    const xml =
      `<?xml version="1.0" encoding="UTF-8"?>\n` +
      `<pedro_run>\n` +
      toXML(summary, "  ") +
      `</pedro_run>\n`;

    downloadText("pedro_last_run.xml", xml);
  };

  return (
    <div className="startup-step-root">
      <h2>
        {isApplyMode
          ? t("APPLY_STEP_DONE_TITLE") || "Apply finished"
          : t("STARTUP_STEP_DONE")}
      </h2>

      <p className="startup-hint">
        {isApplyMode
          ? t("APPLY_STEP_DONE_HINT") ||
            "The apply operation has completed."
          : t("STARTUP_DONE_HINT")}
      </p>

      {/* ========================================================= */}
      {/* ===================== SUMMARY PANEL ==================== */}
      {/* ========================================================= */}

      {!isApplyMode && summary && (
        <div className="startup-summary">

          <div className="summary-block">
            <strong>{t("STARTUP_DONE_DB_LABEL")}</strong>
            <div className="summary-mono">
              {summary.database.db_path}
            </div>
          </div>

          <div className="summary-block">
            <strong>{t("STARTUP_DONE_SOURCE_LABEL")}</strong>
            <div className="summary-mono">
              {summary.paths.source}
            </div>
          </div>

          <div className="summary-block">
            <strong>{t("STARTUP_DONE_TARGET_LABEL")}</strong>
            <div className="summary-mono">
              {summary.paths.target}
            </div>
          </div>

          <div className="summary-block">
            <strong>{t("STARTUP_DONE_MODE_LABEL")}</strong>
            <div>
              {summary.database.mode === "new"
                ? t("STARTUP_DONE_MODE_NEW")
                : t("STARTUP_DONE_MODE_EXISTING")}
            </div>
          </div>

          <div className="summary-block">
            <strong>{t("STARTUP_DONE_OPTIONS_LABEL")}</strong>
            <ul style={{ marginTop: 6 }}>
              <li>
                {t("STARTUP_SCAN_WITH_FINGERPRINT")}:{" "}
                {summary.options?.with_fingerprint ? "✔" : "✖"}
              </li>
              <li>
                {t("STARTUP_SCAN_SEARCH_COVERS")}:{" "}
                {summary.options?.search_covers ? "✔" : "✖"}
              </li>
              <li>
                {t("STARTUP_SCAN_NO_OVERWRITE")}:{" "}
                {summary.options?.no_overwrite ? "✔" : "✖"}
              </li>
            </ul>
          </div>

        </div>
      )}

      {/* ===== APPLY MODE SUMMARY ===== */}
      {isApplyMode && report && (
        <div className="startup-summary">

          <div className="summary-block">
            <strong>Apply result</strong>
            <div>
              Total candidates: {report.summary.total_candidates}
            </div>
            <div>
              Deleted successfully: {report.summary.delete_success_count}
            </div>
            <div>
              Failed deletions: {report.summary.delete_failure_count}
            </div>
          </div>

        </div>
      )}

      {/* ========================================================= */}
      {/* ===================== EXPORT PANEL ===================== */}
      {/* ========================================================= */}

      {!isApplyMode && summary && (
        <div className="startup-info" style={{ marginTop: 16 }}>
          <strong>{t("STARTUP_DONE_EXPORT_TITLE")}</strong>
          <div style={{ marginTop: 8 }}>
            {t("STARTUP_DONE_EXPORT_HINT")}
          </div>

          <div className="startup-actions" style={{ marginTop: 12 }}>
            <button
              className="btn-secondary"
              onClick={handleDownloadJSON}
            >
              {t("STARTUP_DONE_EXPORT_JSON")}
            </button>

            <button
              className="btn-secondary"
              onClick={handleDownloadXML}
            >
              {t("STARTUP_DONE_EXPORT_XML")}
            </button>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* ===================== FINAL ACTIONS ==================== */}
      {/* ========================================================= */}

      <div className="startup-actions" style={{ marginTop: 24 }}>

        {isApplyMode ? (
          <button
            className="btn-primary"
            onClick={onBackToTable}
          >
            {t("APPLY_BACK_TO_TABLE") || "Back to File Table"}
          </button>
        ) : (
          <>
            <button
              className="btn-secondary"
              onClick={onRestartWizard}
            >
              {t("STARTUP_DONE_RESTART")}
            </button>

            <button
              className="btn-primary"
              onClick={onEnterPedro}
            >
              {t("STARTUP_DONE_ENTER_PEDRO")}
            </button>
          </>
        )}

      </div>

      {/* ========================================================= */}
      {/* ================= RAW JSON (COLLAPSIBLE) =============== */}
      {/* ========================================================= */}

      {!isApplyMode && executionPlan && (
        <details style={{ marginTop: 24 }}>
          <summary style={{ cursor: "pointer" }}>
            {t("REVIEW_SHOW_RAW_JSON")}
          </summary>
          <pre className="review-json">
            {JSON.stringify(executionPlan, null, 2)}
          </pre>
        </details>
      )}

      {isApplyMode && report && (
        <details style={{ marginTop: 24 }}>
          <summary style={{ cursor: "pointer" }}>
            Apply report (raw JSON)
          </summary>
          <pre className="review-json">
            {JSON.stringify(report, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}
