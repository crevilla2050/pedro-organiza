import { t } from "../../i18n";

export default function OptionsStep({
  options,
  onSetOptions,
  onBack,
  onNext,
}) {
  /* const options = executionPlan.options; */

  const update = (patch) => {
    onSetOptions({
      ...options,
      ...patch,
    });
  };

  return (
    <div className="startup-step-root">
      <h2>{t("STARTUP_STEP_OPTIONS")}</h2>

      <p className="startup-hint">
        Define how Pedro will apply changes to disk.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 24,
        }}
      >
        {/* ================= LEFT: OPTIONS ================= */}
        <div className="options-panel">
          {/* ===== File operation mode ===== */}
          <div className="options-group">
            <h3>File operations</h3>

            <label className="option-row">
              <input
                type="radio"
                name="operationMode"
                checked={options.operationMode === "copy"}
                onChange={() =>
                  update({ operationMode: "copy" })
                }
              />
              Copy files to target (safe, default)
            </label>

            <label className="option-row">
              <input
                type="radio"
                name="operationMode"
                checked={options.operationMode === "move"}
                onChange={() =>
                  update({ operationMode: "move" })
                }
              />
              Move files to target (destructive)
            </label>
          </div>

          {/* ===== Collision policy ===== */}
          <div className="options-group">
            <h3>When a file already exists</h3>

            <label className="option-row">
              <input
                type="radio"
                name="onCollision"
                checked={options.onCollision === "skip"}
                onChange={() =>
                  update({ onCollision: "skip" })
                }
              />
              Skip this file
            </label>

            <label className="option-row">
              <input
                type="radio"
                name="onCollision"
                checked={options.onCollision === "rename"}
                onChange={() =>
                  update({ onCollision: "rename" })
                }
              />
              Rename new file (append suffix)
            </label>

            <label className="option-row">
              <input
                type="radio"
                name="onCollision"
                checked={options.onCollision === "overwrite"}
                onChange={() =>
                  update({ onCollision: "overwrite" })
                }
              />
              Overwrite existing file (dangerous)
            </label>
          </div>

          {/* ===== Tag writing policy ===== */}
          <div className="options-group">
            <h3>Write tags to audio files</h3>

            <label className="option-row">
              <input
                type="radio"
                name="writeTags"
                checked={options.writeTags === "none"}
                onChange={() =>
                  update({ writeTags: "none" })
                }
              />
              Do not modify tags
            </label>

            <label className="option-row">
              <input
                type="radio"
                name="writeTags"
                checked={options.writeTags === "modified"}
                onChange={() =>
                  update({ writeTags: "modified" })
                }
              />
              Only write tags for modified tracks (recommended)
            </label>

            <label className="option-row">
              <input
                type="radio"
                name="writeTags"
                checked={options.writeTags === "all"}
                onChange={() =>
                  update({ writeTags: "all" })
                }
              />
              Rewrite tags for all tracks
            </label>
          </div>

          {/* ===== Safety toggles ===== */}
          <div className="options-group">
            <h3>Safety</h3>

            <label className="option-row">
              <input
                type="checkbox"
                checked={options.dryRun}
                onChange={(e) =>
                  update({ dryRun: e.target.checked })
                }
              />
              Dry-run only (no disk writes)
            </label>

            <label className="option-row">
              <input
                type="checkbox"
                checked={options.stopOnError}
                onChange={(e) =>
                  update({ stopOnError: e.target.checked })
                }
              />
              Stop on first error
            </label>
          </div>
        </div>

        {/* ================= RIGHT: EXPLANATION ================= */}
        <div className="options-panel">
          <h3>What these options mean</h3>

          <div className="options-explain">
            <p>
              <strong>Copy vs Move:</strong> Copy keeps your original
              library intact. Move will relocate files and should only
              be used when you are fully confident.
            </p>

            <p>
              <strong>Collisions:</strong> Renaming is the safest option
              for repeated batch exports. Overwrite can permanently
              destroy existing files.
            </p>

            <p>
              <strong>Tag writing:</strong> Writing only modified tags
              preserves original metadata while still applying your
              edits.
            </p>

            <p>
              <strong>Dry-run:</strong> Recommended for your first run.
              Pedro will show exactly what it would do, without touching
              the disk.
            </p>
          </div>
        </div>
      </div>

      {/* ================= ACTIONS ================= */}
      <div className="startup-actions">
        <button className="btn-secondary" onClick={onBack}>
          {t("BTN_BACK")}
        </button>

        <button className="btn-primary" onClick={onNext}>
          {t("BTN_NEXT")}
        </button>
      </div>
    </div>
  );
}
