import { useState, Fragment, useRef, useEffect } from "react";
import { usePlayback } from "../context/PlaybackContext";
import { t } from "../i18n";

import BulkSelectionToolbar from "./BulkSelectionToolbar";

const API_BASE = "http://127.0.0.1:8000";

export default function FileTable({
  files,
  loading,
  error,
  onApplySearch,
  onAlpha,
  onGoToApply,
  onSelectionChange,
  onUpdateFile,
}) {
  /* ===================== LOCAL FILTER STATE ===================== */

  const [searchText, setSearchText] = useState("");
  const [searchField, setSearchField] = useState("artist");

  const showLegend = !loading && files.length === 0 && !searchText;

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

  /* ===================== SEARCH ===================== */

  const onApply = () => {
    if (!searchText) return;
    onApplySearch(searchText, searchField);
  };

  const onAlphaClick = (letter) => {
    onAlpha(letter, searchField);
  };

  const onFieldChange = (e) => {
    const newField = e.target.value;
    setSearchField(newField);

    if (searchText) {
      onApplySearch(searchText, newField);
    }
  };

  const onClear = () => {
    setSearchText("");
    setSelectedIds(new Set());
    setEdits({});
  };

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

  const markBulkForDeletion = async () => {
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

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

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

        <div className="pedro-sticky-filter">
          <div className="filter-row">
            <select value={searchField} onChange={onFieldChange}>
              <option value="artist">{t("FIELD_ARTIST")}</option>
              <option value="album">{t("FIELD_ALBUM")}</option>
              <option value="title">{t("FIELD_TITLE")}</option>
            </select>

            <input
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder={t("SEARCH_PLACEHOLDER")}
              onKeyDown={(e) => {
                if (e.key === "Enter") onApply();
              }}
            />

            <button
              className="btn btn-primary"
              onClick={onApply}
              disabled={!searchText}
            >
              {t("APPLY")}
            </button>
          </div>

          <div className="filter-row alpha">
            {"ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").map((letter) => (
              <button
                key={letter}
                className="alpha-btn"
                onClick={() => onAlphaClick(letter)}
              >
                {letter}
              </button>
            ))}

            <button
              className="alpha-btn alpha-all"
              onClick={() => onAlphaClick("#")}
            >
              #
            </button>

            <div className="spacer" />

            <button
              className="btn-clear-filters"
              onClick={onClear}
            >
              {t("CLEAR_FILTERS")}
            </button>

            {onGoToApply && (
              <button
                className="btn btn-sm btn-danger"
                style={{ marginLeft: 10 }}
                onClick={onGoToApply}
              >
                ⚠️ {t("APPLY_DELETIONS")}
              </button>
            )}
          </div>
        </div>

        <div className="pedro-sticky-bulk">
          <BulkSelectionToolbar
            selectedCount={selectedCount}
            onApplyBulkEdit={applyBulkEdits}
            onMarkForDeletion={markBulkForDeletion}
            onClearSelection={clearSelection}
          />
        </div>

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
                                  updateEdit(
                                    row.id,
                                    field,
                                    e.target.value
                                  )
                                }
                                className={
                                  (edit[field] ?? "") !==
                                  (row[field] ?? "")
                                    ? "input-dirty"
                                    : ""
                                }
                              />
                            ))}
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
