import { t } from "../i18n";

function SelectionToolbar({ selection, onClear }) {
  if (!selection.entityIds.length) return null;

  return (
    <div
      className="sticky-top bg-light border-bottom p-2 d-flex align-items-center justify-content-between"
      style={{ zIndex: 1100 }}
    >
      <div>
        <strong>{selection.entityIds.length}</strong>{" "}
        {selection.entityType === "file"
          ? t("TRACKS_SELECTED")
          : t("ITEMS_SELECTED")}
      </div>

      <button
        className="btn btn-sm btn-outline-secondary"
        onClick={onClear}
      >
        {t("CLEAR_SELECTION")}
      </button>
    </div>
  );
}

export default SelectionToolbar;
