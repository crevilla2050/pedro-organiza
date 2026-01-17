import es from "../i18n/es";

const t = (key, vars = {}) => {
  let s = es[key] || key;
  Object.entries(vars).forEach(([k, v]) => {
    s = s.replace(`{${k}}`, v);
  });
  return s;
};

/* ===================== FILTER STATE ===================== */

const [filters, setFilters] = useState({
  q: "",
  field: "artist",
  strict: false,
  caseSensitive: false,
  startsWith: null,
});

const [loadingSearch, setLoadingSearch] = useState(false);

/**
 * FileRow
 * Renders ONE <tr> only. Safe inside <tbody>.
 */
export default function FileRow({
  row,
  isSelected,
  playing,
  onToggleSelect,
  onPlay,
  onJump,
}) {
  if (!row) return null;

  return (
    <tr
      className={[
        row._markDelete ? "table-danger" : "",
        row._ui?.dirty ? "row-dirty" : "",
      ].join(" ")}
    >
      <td style={{ width: 40 }}>
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggleSelect(row.id)}
        />
      </td>

      <td style={{ width: 60 }}>{row.id}</td>
      <td>{row._edit.artist || "-"}</td>
      <td>{row._edit.title || "-"}</td>
      <td>{row._edit.album || "-"}</td>

      <td style={{ width: 160 }}>
        <button
          className="btn btn-sm btn-primary me-1"
          onClick={() => onPlay(row.id)}
        >
          {playing ? t("PAUSE_ICON") : t("PLAY_ICON")}
        </button>
        <button
          className="btn btn-sm btn-outline-dark me-1"
          onClick={() => onJump(-10)}
        >
          −10
        </button>
        <button
          className="btn btn-sm btn-outline-dark"
          onClick={() => onJump(10)}
        >
          +10
        </button>
      </td>
    </tr>
  );
}
