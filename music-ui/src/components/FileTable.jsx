import { Fragment, useState } from "react";
import { usePlayback } from "../context/PlaybackContext";

export default function FileTable({
  files,
  filters,
  loading,
  hasSearched,
  onSearch,
  onClear,
}) {
  const { playTrack, pause, seekBy, playing, currentTrackId } = usePlayback();

  const [selectedIds, setSelectedIds] = useState(new Set());

  const toggleSelect = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div className="file-table-root">

      {/* ================= FILTER BAR ================= */}
      <div className="pedro-sticky-filter">
        <div className="filter-row">
          <select
            value={filters.field}
            onChange={e => onSearch({ field: e.target.value })}
          >
            <option value="artist">Artist</option>
            <option value="album">Album</option>
            <option value="title">Title</option>
          </select>

          <input
            placeholder="Search…"
            value={filters.q}
            onChange={e => onSearch({ q: e.target.value })}
          />

          <button className="btn btn-primary">
            Write to database
          </button>
        </div>

        <div className="filter-row alpha">
          {"ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").map(l => (
            <button
              key={l}
              className="btn btn-sm btn-outline-dark"
              onClick={() => onSearch({ startsWith: l })}
            >
              {l}
            </button>
          ))}

          <button
            className="btn btn-sm btn-outline-dark"
            onClick={() => onSearch({ startsWith: "#" })}
          >
            #
          </button>

          <div className="spacer" />

          <button
            className="btn btn-sm btn-outline-secondary"
            onClick={onClear}
          >
            Clear filters
          </button>
        </div>
      </div>

      {/* ================= RESULTS ================= */}

      {!hasSearched && (
        <div className="table-hint">
          <strong>35k+ files found.</strong><br />
          Please refine your search using the filters above.
        </div>
      )}

      {loading && (
        <div className="table-hint">Searching…</div>
      )}

      {hasSearched && !loading && files.length === 0 && (
        <div className="table-hint">No results.</div>
      )}

      {hasSearched && files.length > 0 && (
        <div className="pedro-scroll-body">
          <table>
            <tbody>
              {files.map(row => {
                const isPlaying =
                  currentTrackId === row.id && playing;

                return (
                  <Fragment key={row.id}>
                    <tr>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(row.id)}
                          onChange={() => toggleSelect(row.id)}
                        />
                      </td>

                      <td>{row.artist || "—"}</td>
                      <td>{row.title || "—"}</td>
                      <td>{row.album || "—"}</td>

                      <td>
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
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
