import { useState } from "react";
import { t } from "../../i18n";

const API_BASE = "http://127.0.0.1:8000";

export default function SourceStep({ onNext, onBack }) {
  const [sourcePath, setSourcePath] = useState("");
  const [loading, setLoading] = useState(false);
  const [inspection, setInspection] = useState(null);
  const [error, setError] = useState(null);

  /* ===================== ACTIONS ===================== */

  const handleInspect = async () => {
    if (!sourcePath) {
      setError(t("STARTUP_SOURCE_NO_PATH"));
      return;
    }

    setLoading(true);
    setError(null);
    setInspection(null);

    try {
      const res = await fetch(`${API_BASE}/startup/inspect-source`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ src: sourcePath }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setInspection(data.inspection || null);
    } catch (err) {
      console.error("Inspect source failed:", err);
      setError(t("STARTUP_SOURCE_INSPECT_FAILED"));
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (!inspection || !inspection.is_acceptable) {
      return;
    }

    // Pass validated path forward
    onNext(sourcePath);
  };

  /* ===================== RENDER ===================== */

  return (
    <div className="startup-step-root">
      <h2>{t("STARTUP_SOURCE_TITLE")}</h2>

      <p className="startup-hint">
        {t("STARTUP_SOURCE_HINT")}
      </p>

      {/* ===== PATH INPUT ===== */}
      <div className="startup-field">
        <label className="startup-label">
          {t("STARTUP_SOURCE_PATH_LABEL")}
        </label>

        <input
          type="text"
          value={sourcePath}
          onChange={(e) => setSourcePath(e.target.value)}
          placeholder={t("STARTUP_SOURCE_PATH_PLACEHOLDER")}
          style={{ width: "100%" }}
        />
      </div>

      {/* ===== ACTION: INSPECT ===== */}
      <div className="startup-actions">
        <button
          className="btn-secondary"
          onClick={handleInspect}
          disabled={loading || !sourcePath}
        >
          {loading ? t("LOADING") : t("STARTUP_BTN_INSPECT_SOURCE")}
        </button>
      </div>

      {/* ===== INSPECTION RESULT ===== */}
      {inspection && (
        <div className="startup-summary">
          <h4>{t("STARTUP_SOURCE_INSPECTION_TITLE")}</h4>

          <ul className="startup-checklist">
            <li>
              {t("STARTUP_SOURCE_VALID_PATH")}:{" "}
              {inspection.is_valid_path ? "✔" : "✘"}
            </li>
            <li>
              {t("STARTUP_SOURCE_IS_DIRECTORY")}:{" "}
              {inspection.is_directory ? "✔" : "✘"}
            </li>
            <li>
              {t("STARTUP_SOURCE_IS_READABLE")}:{" "}
              {inspection.is_readable ? "✔" : "✘"}
            </li>
            <li>
              {t("STARTUP_SOURCE_AUDIO_COUNT")}:{" "}
              {inspection.audio_file_count}
            </li>
          </ul>

          {inspection.warnings && inspection.warnings.length > 0 && (
            <div className="startup-warnings">
              {inspection.warnings.map((w) => (
                <div key={w}>{t(`STARTUP_SOURCE_WARN_${w}`)}</div>
              ))}
            </div>
          )}
        </div>
      )}

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
          disabled={!inspection || !inspection.is_acceptable}
          onClick={handleNext}
        >
          {t("BTN_NEXT")}
        </button>
      </div>
    </div>
  );
}
