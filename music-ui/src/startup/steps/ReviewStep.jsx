import { t } from "../../i18n";

function renderLayoutSummary(layout) {
  const dir = (layout.directory_layout || []).join(" / ");
  const file = (layout.filename_layout || [])
    .map((p) =>
      p.type === "field" ? p.value : JSON.stringify(p.value)
    )
    .join("");

  return {
    directory: dir || t("REVIEW_LAYOUT_EMPTY"),
    filename: file || t("REVIEW_LAYOUT_EMPTY"),
    separateCompilations: layout.separate_compilations ? t("YES") : t("NO"),
  };
}

export default function ReviewStep({
  executionPlan,
  onBack,
  onConfirm,
}) {
  const { database, paths, layout, options } = executionPlan;

  const layoutSummary = renderLayoutSummary(layout);

  const isImported = database.mode === "existing";
  const locked = paths.locked_by_database === true;

  return (
    <div className="startup-step-root">
      <h2>{t("STARTUP_STEP_REVIEW")}</h2>

      <p className="startup-hint">
        {t("REVIEW_HINT")}
      </p>

      <div className="review-grid">

        {/* ===== DATABASE ===== */}
        <div className="review-section">
          <h3>{t("REVIEW_SECTION_DATABASE")}</h3>

          <div className="review-row">
            <span>{t("REVIEW_DB_MODE")}</span>
            <strong>
              {isImported
                ? t("REVIEW_DB_MODE_IMPORTED")
                : t("REVIEW_DB_MODE_NEW")}
            </strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_DB_PATH")}</span>
            <code>{database.db_path || t("REVIEW_VALUE_EMPTY")}</code>
          </div>
        </div>

        {/* ===== PATHS ===== */}
        <div className="review-section">
          <h3>{t("REVIEW_SECTION_PATHS")}</h3>

          <div className="review-row">
            <span>{t("REVIEW_SOURCE_PATH")}</span>
            <code>{paths.source || t("REVIEW_VALUE_EMPTY")}</code>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_TARGET_PATH")}</span>
            <code>{paths.target || t("REVIEW_VALUE_EMPTY")}</code>
            {locked && (
              <div className="review-note">
                {t("REVIEW_IMPORTED_PATHS_NOTE")}
              </div>
            )}
          </div>
          <div className="review-row">
            <span>{t("REVIEW_PATHS_LOCKED")}</span>
            <strong>{locked ? t("YES") : t("NO")}</strong>
          </div>
        </div>

        {/* ===== LAYOUT ===== */}
        <div className="review-section">
          <h3>{t("REVIEW_SECTION_LAYOUT")}</h3>

          <div className="review-row">
            <span>{t("REVIEW_DIR_LAYOUT")}</span>
            <strong>{layoutSummary.directory}</strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_FILE_LAYOUT")}</span>
            <strong>{layoutSummary.filename}</strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_SEPARATE_COMPILATIONS")}</span>
            <strong>{layoutSummary.separateCompilations}</strong>
          </div>
        </div>

        {/* ===== OPTIONS ===== */}
        <div className="review-section">
          <h3>{t("REVIEW_SECTION_OPTIONS")}</h3>

          <div className="review-row">
            <span>{t("REVIEW_DRY_RUN")}</span>
            <strong>{options.dry_run ? t("YES") : t("NO")}</strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_NO_OVERWRITE")}</span>
            <strong>{options.no_overwrite ? t("YES") : t("NO")}</strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_COPY_MODE")}</span>
            <strong>{options.copy_mode}</strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_MAX_PATH_LENGTH")}</span>
            <strong>{options.max_path_length}</strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_SHORTEN_NAMES")}</span>
            <strong>{options.shorten_long_names ? t("YES") : t("NO")}</strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_WITH_FINGERPRINT")}</span>
            <strong>{options.with_fingerprint ? t("YES") : t("NO")}</strong>
          </div>

          <div className="review-row">
            <span>{t("REVIEW_SEARCH_COVERS")}</span>
            <strong>{options.search_covers ? t("YES") : t("NO")}</strong>
          </div>
        </div>
      </div>

      {/* ===== RAW JSON (COLLAPSIBLE) ===== */}
      <details style={{ marginTop: 24 }}>
        <summary style={{ cursor: "pointer" }}>
          {t("REVIEW_SHOW_RAW_JSON")}
        </summary>
        <pre className="review-json">
          {JSON.stringify(executionPlan, null, 2)}
        </pre>
      </details>

      {/* ===== ACTIONS ===== */}
      <div className="startup-actions">
        <button className="btn-secondary" onClick={onBack}>
          {t("BTN_BACK")}
        </button>

        <button className="btn-primary" onClick={onConfirm}>
          {t("REVIEW_BTN_CONFIRM")}
        </button>
      </div>
    </div>
  );
}
