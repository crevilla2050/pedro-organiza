import { t } from "../../i18n";

export default function WelcomeStep({ onSetupNew, onImportDb }) {
  return (
    <div className="startup-step-root">
      <h2>{t("STARTUP_WELCOME_TITLE")}</h2>

      {/* Intro legend */}
      <p className="startup-hint">
        {t("STARTUP_WELCOME_HINT")}
      </p>

      {/* Explanatory bullets */}
      <ul className="startup-bullets">
        <li>{t("STARTUP_WELCOME_BULLET_1")}</li>
        <li>{t("STARTUP_WELCOME_BULLET_2")}</li>
        <li>{t("STARTUP_WELCOME_BULLET_3")}</li>
        <li>{t("STARTUP_WELCOME_BULLET_4")}</li>
      </ul>

      {/* Actions */}
      <div className="startup-actions">
        {/* === Setup New Library === */}
        <button
          className="btn-primary"
          onClick={onSetupNew}
        >
          {t("STARTUP_BTN_SETUP")}
        </button>

        {/* === Import Existing DB === */}
        <button
          className="btn-secondary"
          onClick={onImportDb}
        >
          {t("STARTUP_BTN_IMPORT_DB")}
        </button>
      </div>
    </div>
  );
}
