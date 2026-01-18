import { useState, Fragment, useReducer, useEffect } from "react";
import { usePlayback } from "../context/PlaybackContext";
import { sortReducer, DEFAULT_SORT_STACK } from "../reducers/sortReducer";

const API_BASE = "http://127.0.0.1:8000";

export default function FileTable() {
  /* ===================== PLAYBACK ===================== */
  const { playTrack, pause, seekBy, playing, currentTrackId } = usePlayback();

  /* ===================== SORT ===================== */
  const [sortStack, dispatchSort] = useReducer(
    sortReducer,
    DEFAULT_SORT_STACK
  );

  const sortParam = sortStack
    .map(k => `${k.field}:${k.dir}`)
    .join(",");

  /* ===================== FILTER ===================== */
  const [searchText, setSearchText] = useState("");
  const [searchField, setSearchField] = useState("artist");

  /* ===================== DATA ===================== */
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showLegend, setShowLegend] = useState(true);

  /* ===================== SELECTION ===================== */
  const [selectedIds, setSelectedIds] = useState(new Set());

  const toggleSelect = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  /* ===================== SEARCH ===================== */
  const runSearch = async ({ q, field, startsWith } = {}) => {
    setLoading(true);
    setError(null);
    setShowLegend(false);

    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (field) params.set("field", field);
    if (startsWith) params.set("starts_with", startsWith);
    params.set("sort", sortParam);

    try {
      const res = await fetch(`${API_BASE}/files/search?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRows(Array.isArray(data) ? data : []);
    } catch (err) {
      setError("Search failed");
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  /* re-run search when sort changes */
  useEffect(() => {
    if (!showLegend) {
      runSearch({ q: searchText, field: searchField });
    }
  }, [sortStack]);

  /* ===================== HEADER CELL ===================== */
  const HeaderCell = ({ field, label }) => {
    const key = sortStack.find(k => k.field === field);

    return (
      <div className="col-text header-cell">
        <span
          onClick={() => dispatchSort({ type: "CLICK_COLUMN", field })}
          style={{ cursor: "pointer" }}
        >
          {label} {key?.dir === "asc" ? "▲" : "▼"}
        </span>
        <input
          type="checkbox"
          checked={key?.locked || false}
          onChange={() => dispatchSort({ type: "TOGGLE_LOCK", field })}
          title="Lock sort level"
        />
      </div>
    );
  };

  /* ===================== RENDER ===================== */
  return (
    <div className="file-table-root">

      {/* FILTER BAR */}
      <div className="pedro-sticky-filter">
        <div className="filter-row">
          <select value={searchField} onChange={e => setSearchField(e.target.value)}>
            <option value="artist">Artist</option>
            <option value="album">Album</option>
            <option value="title">Title</option>
          </select>

          <input
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            placeholder="Search…"
            onKeyDown={e => e.key === "Enter" && runSearch({ q: searchText, field: searchField })}
          />

          <button onClick={() => runSearch({ q: searchText, field: searchField })}>
            Apply
          </button>
        </div>

        <div className="filter-row alpha">
          {"ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").map(l => (
            <button key={l} onClick={() => runSearch({ startsWith: l, field: searchField })}>
              {l}
            </button>
          ))}
          <button onClick={() => runSearch({ startsWith: "#", field: searchField })}>#</button>
        </div>
      </div>

      {/* TABLE HEADER */}
      <div className="pedro-sticky-header table-header">
        <div className="col-check">
          <input
            type="checkbox"
            checked={rows.length > 0 && selectedIds.size === rows.length}
            onChange={() => {
              if (selectedIds.size === rows.length) {
                setSelectedIds(new Set());
              } else {
                setSelectedIds(new Set(rows.map(r => r.id)));
              }
            }}
          />
        </div>
        <div className="col-id">ID</div>
        <HeaderCell field="artist" label="Artist" />
        <HeaderCell field="title" label="Title" />
        <HeaderCell field="album" label="Album" />
        <div className="col-preview">Preview</div>
      </div>

      {/* BODY */}
      <div className="pedro-scroll-body">
        {showLegend && (
          <div className="table-hint">
            <strong>35k+</strong> files found — please refine your search
          </div>
        )}

        {loading && <div className="table-hint">Searching…</div>}
        {error && <div className="table-error">{error}</div>}

        {!loading && rows.length > 0 && (
          <table>
            <tbody>
              {rows.map(row => {
                const isPlaying = currentTrackId === row.id && playing;

                return (
                  <tr key={row.id}>
                    <td className="col-check">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(row.id)}
                        onChange={() => toggleSelect(row.id)}
                      />
                    </td>
                    <td className="col-id">{row.id}</td>
                    <td className="col-text">{row.artist || "—"}</td>
                    <td className="col-text">{row.title || "—"}</td>
                    <td className="col-text">{row.album || "—"}</td>
                    <td className="col-preview">
                      <button onClick={() => isPlaying ? pause() : playTrack(row.id, { preview: true })}>
                        {isPlaying ? "❚❚" : "▶"}
                      </button>
                      <button onClick={() => seekBy(-10)}>−10</button>
                      <button onClick={() => seekBy(10)}>+10</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
