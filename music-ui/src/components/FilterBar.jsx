import { t } from "../i18n";

export default function FilterBar({ filters, setFilters }) {
  const { q, field, starts_with } = filters;

  return (
    <div className="pedro-sticky-filter">
      <div className="filter-row">
        <select
          value={field}
          onChange={(e) =>
            setFilters(f => ({
              ...f,
              field: e.target.value,
            }))
          }
        >
          <option value="artist">{t("FIELD_ARTIST")}</option>
          <option value="album">{t("FIELD_ALBUM")}</option>
          <option value="title">{t("FIELD_TITLE")}</option>
        </select>

        <input
          value={q ?? ""}
          placeholder={t("SEARCH_PLACEHOLDER")}
          onChange={(e) =>
            setFilters(f => ({
              ...f,
              q: e.target.value || null,
              starts_with: null,
            }))
          }
        />

        <button
          className="btn btn-primary"
          disabled={!q}
        >
          {t("APPLY")}
        </button>
      </div>

      <div className="filter-row alpha">
        {"ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").map(letter => (
          <button
            key={letter}
            className="alpha-btn"
            onClick={() =>
              setFilters(f => ({
                ...f,
                starts_with: letter,
                q: null,
              }))
            }
          >
            {letter}
          </button>
        ))}

        <button
          className="alpha-btn alpha-all"
          onClick={() =>
            setFilters(f => ({
              ...f,
              starts_with: "#",
              q: null,
            }))
          }
        >
          #
        </button>

        <div className="spacer" />

        <button
          className="btn-clear-filters"
          onClick={() =>
            setFilters(f => ({
              ...f,
              q: null,
              starts_with: null,
              genres: new Set(),
            }))
          }
        >
          {t("CLEAR_FILTERS")}
        </button>
      </div>
    </div>
  );
}
