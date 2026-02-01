import { useState } from "react";
import { t } from "../../i18n";

const API_BASE = "http://127.0.0.1:8000";

export default function ImportDbStep({ onValidDb, onInvalidDb, onBack }) {
  const [dbPath, setDbPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorKey, setErrorKey] = useState(null);
  const [inspection, setInspection] = useState(null);
  const [environment, setEnvironment] = useState(null);

  const runInspection = async () => {
    if (!dbPath) {
      setErrorKey("STARTUP_IMPORT_INVALID_PATH");
      return;
    }

    setLoading(true);
    setErrorKey(null);
    setInspection(null);
    setEnvironment(null);

    try {
      const res = await fetch(`${API_BASE}/startup/inspect-db`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ db_path: dbPath }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();

      const insp = data.inspection || null;
      const env = data.environment || null;

      console.log("IMPORT DB ENV:", env); // ← you already saw this working

      setInspection(insp);
      setEnvironment(env);

    } catch (err) {
      console.error("Inspection failed:", err);
      setErrorKey("STARTUP_IMPORT_INSPECT_FAILED");
    } finally {
      setLoading(false);
    }
  };

  const isValidPedroDb =
    inspection &&
    inspection.is_valid_sqlite &&
    inspection.is_pedro_db;

  return (
    <div className="startup-step-root">
      <h2>{t("STARTUP_STEP_IMPORT_DB")}</h2>

      <p className="startup-hint">
        {t("STARTUP_IMPORT_HINT")}
      </p>

      {/* ===== PATH INPUT ===== */}
      <div className="startup-field">
        <label>{t("STARTUP_DB_PATH_LABEL")}</label>
        <input
          type="text"
          value={dbPath}
          onChange={(e) => {
            setDbPath(e.target.value);
            setInspection(null);
            setEnvironment(null);
            setErrorKey(null);
          }}
          placeholder={t("STARTUP_DB_PATH_PLACEHOLDER")}
          style={{ width: "100%" }}
        />
      </div>

      {/* ===== ACTIONS ===== */}
      <div className="startup-actions">
        <button
          className="btn-secondary"
          onClick={onBack}
          disabled={loading}
        >
          {t("BTN_BACK")}
        </button>

        <button
          className="btn-primary"
          onClick={runInspection}
          disabled={loading || !dbPath}
        >
          {loading ? t("LOADING") : t("STARTUP_BTN_INSPECT_DB")}
        </button>
      </div>

      {/* ===== ERROR ===== */}
      {errorKey && (
        <div className="startup-error">
          {t(errorKey)}
        </div>
      )}

      {/* ===== INSPECTION RESULT ===== */}
      {inspection && (
        <div className="startup-inspection">
          <h3>{t("STARTUP_IMPORT_INSPECTION_TITLE")}</h3>

          <div>
            {t("STARTUP_IMPORT_VALID_PATH")}:{" "}
            {inspection.is_valid_path ? "✔" : "✖"}
          </div>

          <div>
            {t("STARTUP_IMPORT_VALID_SQLITE")}:{" "}
            {inspection.is_valid_sqlite ? "✔" : "✖"}
          </div>

          <div>
            {t("STARTUP_IMPORT_IS_PEDRO_DB")}:{" "}
            {inspection.is_pedro_db ? "✔" : "✖"}
          </div>

          {inspection.warnings &&
            inspection.warnings.length > 0 && (
              <div className="startup-warnings">
                {inspection.warnings.map((w) => (
                  <div key={w}>{t(w)}</div>
                ))}
              </div>
            )}

          {/* ===== DECISION BUTTONS ===== */}
          <div className="startup-actions" style={{ marginTop: 16 }}>
            {isValidPedroDb ? (
              <button
                className="btn-primary"
                onClick={() =>
                  onValidDb({
                    db_path: dbPath,
                    inspection,
                    environment,   // ← THIS WAS MISSING BEFORE
                  })
                }
              >
                {t("STARTUP_BTN_ACTIVATE_DB")}
              </button>
            ) : (
              <button
                className="btn-secondary"
                onClick={onInvalidDb}
              >
                {t("STARTUP_IMPORT_SKIP")}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
