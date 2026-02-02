import { useState } from "react";
import { t } from "../i18n";

/**
 * ApplyPendingBar
 *
 * Global action bar shown when there are pending (dirty) operations.
 * This component is intentionally dumb: it only reflects state and
 * emits user intent upward.
 */
export default function ApplyPendingBar({
  dirtyCount = 0,
  deleteCount = 0,
  onApply,
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  if (dirtyCount === 0 && deleteCount === 0) {
    return null;
  }

  const canApply =
    dirtyCount > 0 &&
    (deleteCount === 0 || confirmDelete);

  return (
    <div className="apply-pending-bar">
      <div className="apply-pending-inner">

        {/* ---- LEFT: summary ---- */}
        <div className="pending-summary">
          {dirtyCount > 0 && (
            <span>
              <strong>{dirtyCount}</strong>{" "}
              {t("PENDING_CHANGES")}
            </span>
          )}

          {deleteCount > 0 && (
            <span className="text-danger">
              <strong>{deleteCount}</strong>{" "}
              {t("FILES_MARKED_FOR_DELETION")}
            </span>
          )}
        </div>

        {/* ---- CENTER: delete confirmation ---- */}
        {deleteCount > 0 && (
          <label className="confirm-delete">
            <input
              type="checkbox"
              checked={confirmDelete}
              onChange={(e) =>
                setConfirmDelete(e.target.checked)
              }
            />
            {t("CONFIRM_DELETION_WARNING")}
          </label>
        )}

        {/* ---- RIGHT: action ---- */}
        <div className="pending-actions">
          <button
            className="btn btn-danger"
            disabled={!canApply}
            onClick={onApply}
          >
            {t("APPLY_PENDING_OPERATIONS")}
          </button>
        </div>
      </div>
    </div>
  );
}
