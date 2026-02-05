import { useState, Fragment, useRef, useEffect } from "react";
import { usePlayback } from "../context/PlaybackContext";
import { t } from "../i18n";

import ApplyPendingBar from "./ApplyPendingBar";
import FilterBar from "./FilterBar";
import BulkSelectionToolbar from "./BulkSelectionToolbar";

const API_BASE = "http://127.0.0.1:8000";

export default function FileTable({
  files,
  loading,
  error,

  /* filters */
  filters,
  setFilters,
  onClearFilters,

  /* pending ops */
  dirtyIds,
  markedForDeletionIds,
  onDirtyChange,
  onMarkedForDeletionChange,

  /* navigation */
  onGoToApply,
  onSelectionChange,
  onUpdateFile,
}) {


  /* ===================== LOCAL FILTER STATE ===================== */

  const showLegend = !loading && files.length === 0;

  /* ===================== PLAYBACK ===================== */

  const {
    playTrack,
    pause,
    seekBy,
    playing,
    currentTrackId,
  } = usePlayback();

  /* ===================== SELECTION STATE ===================== */

  const [selectedIds, setSelectedIds] = useState(new Set());
  const [edits, setEdits] = useState({});

  const selectedCount = selectedIds.size;
  const selectedArray = Array.from(selectedIds);

  const singleSelectedId =
    selectedCount === 1 ? selectedArray[0] : null;

  const bulkSelectedIds =
    selectedCount >= 2 ? selectedArray : [];

  const visibleIds = files.map((r) => r.id);

  const allVisibleSelected =
    visibleIds.length > 0 &&
    visibleIds.every((id) => selectedIds.has(id));

  const someVisibleSelected =
    visibleIds.some((id) => selectedIds.has(id)) &&
    !allVisibleSelected;

  const headerCheckboxRef = useRef(null);

  /* ===================== UI HANDLERS ===================== */

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAllVisible = (checked) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) {
        visibleIds.forEach((id) => next.add(id));
      } else {
        visibleIds.forEach((id) => next.delete(id));
      }
      return next;
    });
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  const updateEdit = (id, field, value) => {
    setEdits((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] || {}),
        [field]: value,
      },
    }));
  };

  /* ===================== DIRTY STATE ===================== */

  const isRowDirty = (row) => {
    const edit = edits[row.id];
    if (!edit) return false;

    return Object.keys(edit).some(
      (key) => (edit[key] ?? "") !== (row[key] ?? "")
    );
  };

  /* ===================== DIRTY PROPAGATION ===================== */

  useEffect(() => {
    if (!onDirtyChange) return;

    const dirtyIds = Object.keys(edits).map(Number);
    onDirtyChange(dirtyIds);
  }, [edits, onDirtyChange]);


  /* ===================== PATCH ===================== */

  const applyRowEdits = async (rowId) => {
    const payload = edits[rowId];
    if (!payload || Object.keys(payload).length === 0) return;

    try {
      const res = await fetch(`${API_BASE}/files/${rowId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      await res.json();

      onUpdateFile(rowId, payload);

      setEdits((prev) => {
        const next = { ...prev };
        delete next[rowId];
        return next;
      });
    } catch (err) {
      console.error("Row update failed:", err);
      alert(t("ROW_APPLY_FAILED"));
    }
  };

  /* ===================== BULK ===================== */

  const applyBulkEdits = async (fields) => {
    if (bulkSelectedIds.length < 2) return;

    const payload = Object.fromEntries(
      Object.entries(fields).filter(([_, v]) => v !== "")
    );

    if (Object.keys(payload).length === 0) return;

    try {
      const res = await fetch(`${API_BASE}/files/bulk`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ids: bulkSelectedIds,
          fields: payload,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      await res.json();

      setSelectedIds(new Set());
      setEdits({});
    } catch (err) {
      console.error("Bulk update failed:", err);
      alert(t("BULK_APPLY_FAILED"));
    }
  };

  const markBulkForDeletion = async (_ignored = null) => {
    if (bulkSelectedIds.length === 0) return;

    try {
      const res = await fetch(`${API_BASE}/files/bulk`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ids: bulkSelectedIds,
          fields: { mark_delete: 1 },
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text);
      }

      await res.json();
      setSelectedIds(new Set());
    } catch (err) {
      console.error("Bulk mark-delete failed:", err);
      alert(t("BULK_APPLY_FAILED"));
    }
  };

  /* ===================== EFFECTS ===================== */

  useEffect(() => {
    if (!onSelectionChange) return;

    onSelectionChange({
      entityType: "file",
      entityIds: Array.from(selectedIds),
    });
  }, [selectedIds, onSelectionChange]);

  useEffect(() => {
    if (headerCheckboxRef.current) {
      headerCheckboxRef.current.indeterminate = someVisibleSelected;
    }
  }, [someVisibleSelected, allVisibleSelected]);

  /* ===================== RENDER ===================== */

  return (
    <div className="file-table-root">
      <div className="pedro-fixed-header">
        <div className="pedro-sticky-bulk">
          <FilterBar
            filters={filters}
            setFilters={setFilters}
          />
          <ApplyPendingBar
            dirtyIds={dirtyIds}
            markedForDeletionIds={markedForDeletionIds}
            onApply={onGoToApply}
          />
          <BulkSelectionToolbar
            selectedCount={selectedCount}
            onApplyBulkEdit={applyBulkEdits}
            onMarkForDeletion={markBulkForDeletion}
            onClearSelection={clearSelection}
          />
        </div>
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={onClearFilters}
        >
          {t("CLEAR_FILTERS")}
        </button>
        <div className="pedro-sticky-header table-header">
          <div className="col-check">
            <input
              ref={headerCheckboxRef}
              type="checkbox"
              checked={allVisibleSelected}
              onChange={(e) =>
                toggleSelectAllVisible(e.target.checked)
              }
            />
          </div>
          
          <div className="col-id">ID</div>
          <div className="col-text">{t("FIELD_ARTIST")}</div>
          <div className="col-text">{t("FIELD_TITLE")}</div>
          <div className="col-text">{t("FIELD_ALBUM")}</div>
            
          <div className="col-preview">{t("PREVIEW")}</div>
          
        </div>
      </div>
      <div className="pedro-scroll-body">
        {showLegend && (
          <div className="table-hint">
            <strong>35k+</strong> {t("REFINE_SEARCH_HINT")}
          </div>
        )}

        {loading && <div className="table-hint">{t("SEARCHING")}</div>}
        {error && <div className="table-error">{error}</div>}

        {!loading && files.length > 0 && (
          <table>
            <tbody>
              {files.map((row) => {
                const isSelected = selectedIds.has(row.id);
                const isExpanded = row.id === singleSelectedId;
                const edit = edits[row.id] || {};
                const isPlaying =
                  currentTrackId === row.id && playing;

                return (
                  <Fragment key={row.id}>
                    <tr
                      className={[
                        isSelected ? "row-selected" : "",
                        isRowDirty(row) ? "row-dirty" : "",
                      ].join(" ")}
                    >
                      <td className="col-check">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onClick={(e) => e.stopPropagation()}
                          onChange={() => toggleSelect(row.id)}
                        />
                      </td>

                      <td className="col-id">
                        {row.id}

                        {isRowDirty(row) && (
                          <span className="dirty-star">*</span>
                        )}
                      </td>

                      {["artist", "title", "album"].map((field) => (
                        <td key={field} className="col-text">
                          {isExpanded ? (
                            <input
                              className={
                                edit[field] !== undefined
                                  ? "input-dirty"
                                  : ""
                              }
                              value={edit[field] ?? row[field] ?? ""}
                              onChange={(e) =>
                                updateEdit(
                                  row.id,
                                  field,
                                  e.target.value
                                )
                              }
                            />
                          ) : (
                            row[field] || "—"
                          )}
                        </td>
                      ))}

                      <td className="col-preview">
                        <button
                          className={[
                            "preview",
                            isPlaying ? "playing" : "",
                          ].join(" ")}
                          onClick={(e) => {
                            e.stopPropagation();
                            isPlaying
                              ? pause()
                              : playTrack(row.id, { preview: true });
                          }}
                        >
                          {isPlaying ? "❚❚" : "▶"}
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            seekBy(-10);
                          }}
                        >
                          −10
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            seekBy(10);
                          }}
                        >
                          +10
                        </button>
                      </td>

                    </tr>
                    {isExpanded && (
                      <tr className="expanded">
                        <td colSpan={6}>
                          <div className="expanded-grid">
                            {[
                              ["album_artist", "FIELD_ALBUM_ARTIST"],
                              ["track", "FIELD_TRACK"],
                              ["year", "FIELD_YEAR"],
                              ["bpm", "FIELD_BPM"],
                              ["composer", "FIELD_COMPOSER"],
                            ].map(([field, key]) => (
                              <input
                                key={field}
                                placeholder={t(key)}
                                value={edit[field] ?? row[field] ?? ""}
                                onChange={(e) =>
                                  updateEdit(row.id, field, e.target.value)
                                }
                                className={
                                  (edit[field] ?? "") !== (row[field] ?? "")
                                    ? "input-dirty"
                                    : ""
                                }
                              />
                            ))}
                            
                            {/* MARK FOR DELETION */}
                            <label
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: 4,
                                marginLeft: 6,
                                fontSize: "0.75em",
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={
                                  edit.mark_delete !== undefined
                                    ? Boolean(edit.mark_delete)
                                    : Boolean(row.mark_delete)
                                }
                                onChange={(e) =>
                                  updateEdit(
                                    row.id,
                                    "mark_delete",
                                    e.target.checked ? 1 : 0
                                  )
                                }
                              />
                              {t("MARK_FOR_DELETION")}
                            </label>

                            {/* IS COMPILATION */}
                            <label className="checkbox-field">
                              <input
                                type="checkbox"
                                checked={
                                  edit.is_compilation ??
                                  Boolean(row.is_compilation)
                                }
                                onChange={(e) =>
                                  updateEdit(
                                    row.id,
                                    "is_compilation",
                                    e.target.checked ? 1 : 0
                                  )
                                }
                              />
                              {t("FIELD_IS_COMPILATION")}
                            </label>
                          </div>


                          <div className="expanded-actions">
                            {isRowDirty(row) && (
                              <button
                                className="btn btn-primary"
                                onClick={() =>
                                  applyRowEdits(row.id)
                                }
                              >
                                {t("APPLY")}
                              </button>
                            )}
                          </div>

                          <div className="expanded-path">
                            {row.original_path}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
