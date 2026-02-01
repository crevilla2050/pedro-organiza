import { useEffect, useState } from "react";
import { t } from "./i18n";
import pedroLogoBig from "./assets/logo.png";

const API_BASE = "http://127.0.0.1:8000";

export default function LandingPage({ onEnterWizard, onEnterDirect }) {
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [info, setInfo] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/startup/landing-status`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        setInfo(data);
        setStatus("ready");
      } catch (err) {
        console.error("Landing status failed:", err);
        setStatus("error");
      }
    })();
  }, []);

  const canEnterDirect = info?.can_enter === true;

  return (
    <div className="startup-root">
      <div className="startup-header">
        <img
          src={pedroLogoBig}
          alt={t("APP_NAME")}
          className="startup-logo"
        />

        <div style={{ flex: 1 }}>
          <h1>{t("APP_NAME")}</h1>
          <p className="startup-subtitle">
            {t("LANDING_SUBTITLE")}
          </p>
        </div>
      </div>

      <div className="startup-body" style={{ alignItems: "center" }}>
        {status === "loading" && (
          <div className="startup-info">
            {t("LANDING_CHECKING_ENV")}
          </div>
        )}

        {status === "error" && (
          <div className="startup-error">
            {t("ERROR_GENERIC")}
          </div>
        )}

        {status === "ready" && (
          <div style={{ marginTop: 40, textAlign: "center" }}>

            {canEnterDirect && (
              <div style={{ marginBottom: 12, opacity: 0.7 }}>
                {t("LANDING_USING_DB")}:<br />
                <code>{info.db_path}</code>
              </div>
            )}

            <div className="startup-actions" style={{ justifyContent: "center" }}>
              <button
                className="btn-primary"
                onClick={onEnterWizard}
              >
                {t("LANDING_ENTER_WIZARD")}
              </button>

              <button
                className="btn-secondary"
                style={{ marginLeft: 12 }}
                disabled={!canEnterDirect}
                onClick={onEnterDirect}
                title={
                  canEnterDirect
                    ? ""
                    : t("LANDING_DIRECT_DISABLED_HINT")
                }
              >
                {t("LANDING_ENTER_DIRECT")}
              </button>
            </div>

            {!canEnterDirect && (
              <div style={{ marginTop: 16, opacity: 0.7 }}>
                {t("LANDING_NO_DB_HINT")}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
