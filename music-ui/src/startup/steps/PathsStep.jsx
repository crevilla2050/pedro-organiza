import { useState } from "react";
import { t } from "../../i18n";

const API_BASE = "http://127.0.0.1:8000";

export default function PathsStep({
  executionPlan,
  onUpdate,
  onBack,
  onNext,
}) {
  const { paths } = executionPlan;

  const [loadingSource, setLoadingSource] = useState(false);
  const [loadingTarget, setLoadingTarget] = useState(false);
  const [error, setError] = useState(null);

  const sourcePath = paths.source || "";
  const targetPath = paths.target || "";
  const sourceInspection = paths.source_inspection;
  const targetInspection = paths.target_inspection;

  /* =====================
     Inspect Source
  ===================== */

  const inspectSource = async () => {
    if (!sourcePath) return;

    setLoadingSource(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/startup/inspect-source`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ src: sourcePath }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();

      onUpdate({
        source_inspection: data.inspection,
        // Invalidate target if source changes
        target_inspection: null,
      });
    } catch (err) {
      console.error("inspect-source failed:", err);
      setError(t("ERROR_GENERIC"));
    } finally {
      setLoadingSource(false);
    }
  };

  /* =====================
     Inspect Target
  ===================== */

  const inspectTarget = async () => {
    if (!sourcePath || !targetPath) return;

    setLoadingTarget(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/startup/inspect-target`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          src: sourcePath,
          dst: targetPath,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();

      onUpdate({
        target_inspection: data.inspection,
      });
    } catch (err) {
      console.error("inspect-target failed:", err);
      setError(t("ERROR_GENERIC"));
    } finally {
      setLoadingTarget(false);
    }
  };

  /* =====================
     Validation
  ===================== */

  const sourceAcceptable =
    sourceInspection && sourceInspection.is_acceptable === true;

  const targetAcceptable =
    targetInspection && targetInspection.is_acceptable === true;

  const canContinue = sourceAcceptable && targetAcceptable;

  /* =====================
     Render helpers
  ===================== */

  const renderSourceInspection = () => {
    if (!sourceInspection) return null;

    return (
      <div className="startup-inspection">
        <div>
          {t("STARTUP_IMPORT_VALID_PATH")}:{" "}
          {sourceInspection.is_valid_path ? "✔" : "✖"}
        </div>
        <div>
          {t("STARTUP_SOURCE_IS_DIRECTORY")}:{" "}
          {sourceInspection.is_directory ? "✔" : "✖"}
        </div>
        <div>
          {t("STARTUP_SOURCE_IS_READABLE")}:{" "}
          {sourceInspection.is_readable ? "✔" : "✖"}
        </div>
        <div>
          {t("STARTUP_SOURCE_AUDIO_COUNT")}:{" "}
          {sourceInspection.audio_file_count}
        </div>

        {sourceInspection.warnings &&
          sourceInspection.warnings.length > 0 && (
            <div className="startup-warnings">
              {sourceInspection.warnings.map((w) => (
                <div key={w}>{t(w)}</div>
              ))}
            </div>
          )}
      </div>
    );
  };

  const renderTargetInspection = () => {
    if (!targetInspection) return null;

    return (
      <div className="startup-inspection">
        <div>
          {t("STARTUP_TARGET_VALID_PATH")}:{" "}
          {targetInspection.is_valid_path ? "✔" : "✖"}
        </div>
        <div>
          {t("STARTUP_TARGET_IS_DIRECTORY")}:{" "}
          {targetInspection.is_directory ? "✔" : "✖"}
        </div>
        <div>
          {t("STARTUP_TARGET_IS_WRITABLE")}:{" "}
          {targetInspection.is_writable ? "✔" : "✖"}
        </div>
        <div>
          {t("STARTUP_TARGET_IS_EMPTY")}:{" "}
          {targetInspection.is_empty === null
            ? "—"
            : targetInspection.is_empty
            ? "✔"
            : "✖"}
        </div>

        {targetInspection.warnings &&
          targetInspection.warnings.length > 0 && (
            <div className="startup-warnings">
              {targetInspection.warnings.map((w) => (
                <div key={w}>{t(w)}</div>
              ))}
            </div>
          )}
      </div>
    );
  };

  /* =====================
     Render
  ===================== */

  return (
    <div className="startup-step-root">
      <h2>{t("STARTUP_STEP_SOURCE")}</h2>

      <p className="startup-hint">
        {t("STARTUP_PATHS_HINT")}
      </p>

      {/* ===== SOURCE PATH ===== */}
      <div className="startup-field">
        <label>{t("STARTUP_SOURCE_PATH_LABEL")}</label>
        <input
          type="text"
          value={sourcePath}
          onChange={(e) =>
            onUpdate({
              ...paths,
              source: e.target.value,
              source_inspection: null,
              target_inspection: null,
            })
          }
          placeholder={t("STARTUP_SOURCE_PATH_PLACEHOLDER")}
          style={{ width: "100%" }}
        />

        <div className="startup-actions">
          <button
            className="btn-secondary"
            disabled={!sourcePath || loadingSource}
            onClick={inspectSource}
          >
            {loadingSource
              ? t("LOADING")
              : t("STARTUP_BTN_INSPECT_SOURCE")}
          </button>
        </div>

        {renderSourceInspection()}
      </div>

      {/* ===== TARGET PATH ===== */}
      <div className="startup-field">
        <label>{t("STARTUP_TARGET_PATH_LABEL")}</label>
        <input
          type="text"
          value={targetPath}
          onChange={(e) =>
            onUpdate({
              ...paths,
              target: e.target.value,
              target_inspection: null,
            })
          }
          placeholder={t("STARTUP_TARGET_PATH_PLACEHOLDER")}
          style={{ width: "100%" }}
          disabled={!sourceAcceptable}
        />

        <div className="startup-actions">
          <button
            className="btn-secondary"
            disabled={
              !sourceAcceptable ||
              !targetPath ||
              loadingTarget
            }
            onClick={inspectTarget}
          >
            {loadingTarget
              ? t("LOADING")
              : t("STARTUP_BTN_INSPECT_TARGET")}
          </button>
        </div>

        {renderTargetInspection()}
      </div>

      {/* ===== ERROR ===== */}
      {error && (
        <div className="startup-error">
          {error}
        </div>
      )}

      {/* ===== ACTIONS ===== */}
      <div className="startup-actions">
        <button
          className="btn-secondary"
          onClick={onBack}
        >
          {t("BTN_BACK")}
        </button>

        <button
          className="btn-primary"
          disabled={!canContinue}
          onClick={onNext}
        >
          {t("BTN_NEXT")}
        </button>
      </div>
    </div>
  );
}
