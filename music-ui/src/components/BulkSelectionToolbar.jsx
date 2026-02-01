import { useState } from "react";
import { t } from "../i18n";

function BulkSelectionToolbar({
  selectedCount,
  onApplyBulkEdit,
  onMarkForDeletion,
  onClearSelection,
}) {
  // Always run hooks
  const [bulkEdit, setBulkEdit] = useState({
    artist: "",
    album: "",
    title: "",
    year: "",
    is_compilation: null, // 👈 tri-state
  });

  // Render nothing unless meaningful
  if (selectedCount < 2) return null;

  const apply = () => {
    const payload = Object.fromEntries(
      Object.entries(bulkEdit).filter(
        ([_, v]) => v !== "" && v !== null
      )
    );

    if (Object.keys(payload).length === 0) return;

    onApplyBulkEdit(payload);

    setBulkEdit({
      artist: "",
      album: "",
      title: "",
      year: "",
      is_compilation: null,
    });
  };

  const hasEdits = Object.values(bulkEdit).some(
    v => v !== "" && v !== null
  );

  return (
    <div className="bulk-toolbar pedro-bulk-toolbar sticky-top">
      <div className="d-flex align-items-center gap-2 flex-nowrap">

        {/* ---- selection info ---- */}
        <div className="bulk-info text-muted">
          <strong>{selectedCount}</strong> {t("ITEMS_SELECTED")}
        </div>

        {/* ---- bulk fields ---- */}
        <div className="d-flex align-items-center gap-2 flex-grow-1">

          <input
            className="form-control form-control-sm"
            placeholder={t("FIELD_ARTIST")}
            value={bulkEdit.artist}
            onChange={e =>
              setBulkEdit(b => ({ ...b, artist: e.target.value }))
            }
          />

          <input
            className="form-control form-control-sm"
            placeholder={t("FIELD_ALBUM")}
            value={bulkEdit.album}
            onChange={e =>
              setBulkEdit(b => ({ ...b, album: e.target.value }))
            }
          />

          <input
            className="form-control form-control-sm"
            placeholder={t("FIELD_TITLE")}
            value={bulkEdit.title}
            onChange={e =>
              setBulkEdit(b => ({ ...b, title: e.target.value }))
            }
          />

          <input
            className="form-control form-control-sm"
            placeholder={t("FIELD_YEAR")}
            style={{ maxWidth: 90 }}
            value={bulkEdit.year}
            onChange={e =>
              setBulkEdit(b => ({ ...b, year: e.target.value }))
            }
          />

          {/* BULK IS COMPILATION */}
          <label className="bulk-checkbox">
            <input
              type="checkbox"
              checked={bulkEdit.is_compilation === 1}
              onChange={e =>
                setBulkEdit(b => ({
                  ...b,
                  is_compilation: e.target.checked ? 1 : 0,
                }))
              }
            />
            {t("FIELD_IS_COMPILATION")}
          </label>
        </div>

        {/* ---- actions ---- */}
        <div className="d-flex align-items-center gap-2">

          <button
            className="btn btn-sm btn-success"
            disabled={!hasEdits}
            onClick={apply}
          >
            {t("APPLY")}
          </button>
          
          {/* bulk mark-for-deletion */}
          <button
            className="btn btn-sm btn-outline-danger"
            onClick={onMarkForDeletion} 
            title={t("MARK_FOR_DELETION")}
          >
            🗑
          </button>

          <button
            className="btn btn-sm btn-outline-secondary"
            onClick={onClearSelection}
            title={t("CLEAR_SELECTION")}
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}

export default BulkSelectionToolbar;
