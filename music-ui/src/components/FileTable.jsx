import { useState, Fragment } from "react";
import { usePlayback } from "../context/PlaybackContext";
import { t } from "../i18n";

const API_BASE = "http://127.0.0.1:8000";

export default function FileTable() {

  /* ===================== PLAYBACK ===================== */

  const {
    playTrack,
    pause,
    seekBy,
    playing,
    currentTrackId,
  } = usePlayback();

  /* ===================== FILTER STATE ===================== */

  const [searchText, setSearchText] = useState("");
  const [searchField, setSearchField] = useState("artist");
  const [rows, setRows] = useState([]);
  const [showLegend, setShowLegend] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /* ===================== SELECTION STATE ===================== */

  const [selectedIds, setSelectedIds] = useState(new Set());
  const [edits, setEdits] = useState({});
  const [bulkEdit, setBulkEdit] = useState({ disc: "" });

  /* ---------- Derived selection ---------- */

  const selectedCount = selectedIds.size;
  const singleSelectedId =
    selectedCount === 1 ? Array.from(selectedIds)[0] : null;
  const bulkSelectedIds =
    selectedCount >= 2 ? Array.from(selectedIds) : [];

  const bulkEnabled = bulkSelectedIds.length >= 2;

  /* ===================== SEARCH CORE ===================== */

  const runSearch = async ({ q, field, startsWith = null }) => {
    if (!q && !startsWith) {
      setRows([]);
      setShowLegend(true);
      return;
    }

    setLoading(true);
    setError(null);
    setShowLegend(false);
    setSelectedIds(new Set());
    setEdits({});

    try {
      let url = `${API_BASE}/files/search?field=${field}`;

      if (startsWith) {
        url += `&starts_with=${encodeURIComponent(startsWith)}`;
      } else if (q) {
        url += `&q=${encodeURIComponent(q)}`;
      }

      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setRows(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Search failed:", err);
      setError(t("SEARCH_FAILED"));
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  /* ===================== UI HANDLERS ===================== */

  const toggleSelect = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const updateEdit = (id, field, value) => {
    setEdits(prev => ({
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
      key => (edit[key] ?? "") !== (row[key] ?? "")
    );
  };

  const onApply = () => {
    runSearch({ q: searchText, field: searchField });
  };

  const onAlphaClick = (letter) => {
    runSearch({ field: searchField, startsWith: letter });
  };

  const onFieldChange = (e) => {
    const newField = e.target.value;
    setSearchField(newField);

    if (searchText) {
      runSearch({ q: searchText, field: newField });
    }
  };

  const onClearFilters = () => {
    setSearchText("");
    setRows([]);
    setShowLegend(true);
    setError(null);
    setSelectedIds(new Set());
    setEdits({});
  };

  /* ===================== PATCH HELPERS ===================== */

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

      const data = await res.json();

      setRows(prev =>
        prev.map(r => (r.id === rowId ? data.file : r))
      );

      setEdits(prev => {
        const next = { ...prev };
        delete next[rowId];
        return next;
      });

    } catch (err) {
      console.error("Row update failed:", err);
      alert(t("ROW_APPLY_FAILED"));
    }
  };

  const applyBulkEdits = async () => {
    if (!bulkEnabled) return;

    const payload = Object.fromEntries(
      Object.entries(bulkEdit).filter(([_, v]) => v !== "")
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

      setRows(prev =>
        prev.map(r =>
          bulkSelectedIds.includes(r.id)
            ? { ...r, ...payload }
            : r
        )
      );

      setBulkEdit({ disc: "" });
      setSelectedIds(new Set());
      setEdits({});

    } catch (err) {
      console.error("Bulk update failed:", err);
      alert(t("BULK_APPLY_FAILED"));
    }
  };

  /* ===================== RENDER ===================== */

  return (
    <div className="file-table-root">

      {/* ================= FILTER BAR ================= */}
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
          {"ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").map(letter => (
            <button
              key={letter}
              className="btn btn-sm btn-outline-dark"
              onClick={() => onAlphaClick(letter)}
            >
              {letter}
            </button>
          ))}

          <button
            className="btn btn-sm btn-outline-dark"
            onClick={() => onAlphaClick("#")}
          >
            #
          </button>

          <div className="spacer" />

          <button
            className="btn btn-sm btn-outline-secondary"
            onClick={onClearFilters}
          >
            {t("CLEAR_FILTERS")}
          </button>
        </div>
      </div>

      {/* ================= BULK EDIT BAR ================= */}
      <div className={`pedro-sticky-bulk ${bulkEnabled ? "" : "disabled"}`}>
        <div className="bulk-row primary">
          <input placeholder={t("FIELD_ARTIST")} disabled />
          <input placeholder={t("FIELD_ALBUM")} disabled />
          <input placeholder={t("FIELD_ALBUM_ARTIST")} disabled />
          <input placeholder={t("FIELD_YEAR")} disabled />
          <input placeholder={t("FIELD_BPM")} disabled />
          <input
            placeholder={t("FIELD_DISC")}
            disabled={!bulkEnabled}
            value={bulkEdit.disc}
            onChange={e =>
              setBulkEdit(p => ({ ...p, disc: e.target.value }))
            }
          />
        </div>

        <div className="bulk-row secondary">
          <label>
            <input type="checkbox" disabled />
            {t("FIELD_COMPILATION")}
          </label>

          <label className="mark-delete">
            <input type="checkbox" disabled />
            {t("MARK_FOR_DELETION")}
          </label>

          <button
            disabled={!bulkEnabled}
            onClick={applyBulkEdits}
          >
            {t("APPLY")}
          </button>
        </div>
      </div>

      {/* ================= TABLE HEADER ================= */}
      <div className="pedro-sticky-header table-header">
        <div className="col-check" />
        <div className="col-id">ID</div>
        <div className="col-text">{t("FIELD_ARTIST")}</div>
        <div className="col-text">{t("FIELD_TITLE")}</div>
        <div className="col-text">{t("FIELD_ALBUM")}</div>
        <div className="col-preview">{t("PREVIEW")}</div>
      </div>

      {/* ================= BODY ================= */}
      <div className="pedro-scroll-body">

        {showLegend && (
          <div className="table-hint">
            <strong>35k+</strong> {t("REFINE_SEARCH_HINT")}
          </div>
        )}

        {loading && (
          <div className="table-hint">{t("SEARCHING")}</div>
        )}

        {error && (
          <div className="table-error">{error}</div>
        )}

        {!loading && rows.length > 0 && (
          <table>
            <tbody>
              {rows.map(row => {
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
                          onChange={() => toggleSelect(row.id)}
                        />
                      </td>

                      <td className="col-id">
                        {row.id}
                        {isRowDirty(row) && (
                          <span className="dirty-star">*</span>
                        )}
                      </td>

                      {["artist", "title", "album"].map(field => (
                        <td key={field} className="col-text">
                          {isExpanded ? (
                            <input
                              className={
                                edit[field] !== undefined
                                  ? "input-dirty"
                                  : ""
                              }
                              value={edit[field] ?? row[field] ?? ""}
                              onChange={e =>
                                updateEdit(row.id, field, e.target.value)
                              }
                            />
                          ) : (
                            row[field] || "—"
                          )}
                        </td>
                      ))}

                      <td className="col-preview">
                        <button
                          onClick={() =>
                            isPlaying
                              ? pause()
                              : playTrack(row.id, { preview: true })
                          }
                        >
                          {isPlaying ? "❚❚" : "▶"}
                        </button>

                        <button onClick={() => seekBy(-10)}>−10</button>
                        <button onClick={() => seekBy(10)}>+10</button>
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
                                onChange={e =>
                                  updateEdit(row.id, field, e.target.value)
                                }
                                className={
                                  (edit[field] ?? "") !== (row[field] ?? "")
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
                                onClick={() => applyRowEdits(row.id)}
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
