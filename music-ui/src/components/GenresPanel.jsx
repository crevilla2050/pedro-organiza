import { useEffect, useMemo, useState } from "react";
import { t } from "../i18n";

const API_BASE = "http://127.0.0.1:8000";

function GenresPanel({
  selection,
  activeGenres,        // Set<string>
  onFilterGenres,      // setter
}) {
  const [state, setState] = useState({
    applied: [],
    partial: [],
    available: [],
  });

  const [checked, setChecked] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [genreQuery, setGenreQuery] = useState("");

  const filterMode = selection.entityIds.length === 0;
  const safeActiveGenres =
    activeGenres instanceof Set ? activeGenres : new Set();

  /* ---------- selected genres (normalization) ---------- */

  const selectedGenres = useMemo(() => {
    return [
      ...state.applied,
      ...state.partial,
      ...state.available,
    ].filter((g) => checked.has(g.id));
  }, [state, checked]);

  const canNormalize = !filterMode && selectedGenres.length >= 2;

  const [showNormalize, setShowNormalize] = useState(false);
  const [normalizeName, setNormalizeName] = useState("");
  const [normalizing, setNormalizing] = useState(false);
  const [normalizeError, setNormalizeError] = useState(null);

  /* ---------- normalize ---------- */

  const normalizeGenres = async () => {
    if (!canNormalize || !normalizeName.trim()) return;

    setNormalizing(true);
    setNormalizeError(null);

    try {
      await fetch(`${API_BASE}/api/genres/normalize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          old_genre_ids: selectedGenres.map((g) => g.id),
          canonical_name: normalizeName.trim(),
        }),
      });

      const refreshed = await fetch(
        `${API_BASE}/side-panel/genres?entity_type=${selection.entityType}&entity_ids=${selection.entityIds.join(",")}`
      ).then((r) => r.json());

      setState(refreshed);
      setChecked(new Set(refreshed.applied.map((g) => g.id)));
      setDirty(false);
      setShowNormalize(false);
      setNormalizeName("");

    } catch (e) {
      setNormalizeError(e?.message || "Normalization failed");
    } finally {
      setNormalizing(false);
    }
  };

  /* ---------- load state ---------- */

  useEffect(() => {
    setLoading(true);

    if (filterMode) {
      fetch(`${API_BASE}/genres?include_usage=true`)
        .then((r) => r.json())
        .then((data) => {
          const nonEmpty = data.filter(g => g.file_count > 0);

          setState({
            applied: [],
            partial: [],
            available: nonEmpty,
          });

          setChecked(new Set());
          setDirty(false);
        })
        .finally(() => setLoading(false));
      return;
    }

    fetch(
      `${API_BASE}/side-panel/genres?entity_type=${selection.entityType}&entity_ids=${selection.entityIds.join(",")}`
    )
      .then((r) => r.json())
      .then((data) => {
        setState(data);
        setChecked(new Set(data.applied.map((g) => g.id))); // ✅ only here
        setDirty(false);
      })
      .finally(() => setLoading(false));
  }, [selection, filterMode]);

  /* ---------- reset normalize UI only ---------- */

  useEffect(() => {
    if (!canNormalize) {
      setShowNormalize(false);
      setNormalizeName("");
      setNormalizeError(null);
    }
  }, [canNormalize]);

  /* ---------- handlers ---------- */

  const toggleEdit = (id) => {
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
    setDirty(true);
  };

  const toggleFilter = (name) => {
    onFilterGenres((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  const toggleGenre = (genreName) => {
    onFilterGenres(prev => {
      const next = new Set(prev);
      next.has(genreName)
        ? next.delete(genreName)
        : next.add(genreName);
      return next;
    });
  };

  const applyChanges = async () => {
    const current = new Set(state.applied.map((g) => g.id));
    const toAdd = [...checked].filter((id) => !current.has(id));
    const toRemove = [...current].filter((id) => !checked.has(id));

    if (!toAdd.length && !toRemove.length) return;

    setLoading(true);

    await fetch(`${API_BASE}/side-panel/genres/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entity_ids: selection.entityIds,
        add: toAdd,
        remove: toRemove,
      }),
    });

    const refreshed = await fetch(
      `${API_BASE}/side-panel/genres?entity_type=${selection.entityType}&entity_ids=${selection.entityIds.join(",")}`
    ).then((r) => r.json());

    setState(refreshed);
    setChecked(new Set(refreshed.applied.map((g) => g.id)));
    setDirty(false);
    setLoading(false);
    await reloadGenresPanel();
  };

  /* ---------- render ---------- */

  const allGenres = [
    ...state.applied,
    ...state.partial,
    ...state.available,
  ].filter((g) =>
    g.name.toLowerCase().includes(genreQuery.toLowerCase())
  );

  const reloadGenresPanel = async () => {
    if (filterMode) {
      const all = await fetch(
        `${API_BASE}/genres?include_usage=true`
      ).then(r => r.json());

      const nonEmpty = all.filter(g => g.file_count > 0);

      setState({
        applied: [],
        partial: [],
        available: nonEmpty,
      });

      setChecked(new Set());
      setDirty(false);
    } else {
      const refreshed = await fetch(
        `${API_BASE}/side-panel/genres?entity_type=${selection.entityType}&entity_ids=${selection.entityIds.join(",")}`
      ).then(r => r.json());

      setState(refreshed);
      setChecked(new Set(refreshed.applied.map(g => g.id)));
      setDirty(false);
    }
    await reloadGenresPanel();
  };

  const handleApplyClick = async () => {
    await applyChanges();
    await reloadGenresPanel();
  };


  return (
    <>
      <div className="p-2 border-bottom genres-panel">
        <strong>{t("GENRES_TITLE")}</strong>

        <input
          className="form-control form-control-sm mb-2"
          placeholder={t("GENRES_SEARCH_PLACEHOLDER")}
          value={genreQuery}
          onChange={(e) => setGenreQuery(e.target.value)}
        />

        {loading && <div className="small text-muted">{t("LOADING")}</div>}

        <div className="genres-grid">
          {allGenres.map((g) => {
            const isChecked = filterMode
              ? safeActiveGenres.has(g.name)
              : checked.has(g.id);

            return (
              <label
                key={g.id}
                className={`genre-item ${
                  filterMode && isChecked ? "genre-active" : ""
                } ${!filterMode && isChecked ? "genre-selected" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() =>
                    filterMode ? toggleFilter(g.name) : toggleEdit(g.id)
                  }
                />
                <span className="genre-name">{g.name}</span>
              </label>
            );
          })}
        </div>

        {!filterMode && canNormalize && !showNormalize && (
          <button
            className="btn btn-sm btn-warning mt-2 me-2"
            onClick={() => setShowNormalize(true)}
          >
            {t("NORMALIZE")}
          </button>
        )}

        {!filterMode && (
          <button
            className="btn btn-sm btn-success mt-2"
            disabled={!dirty || loading}
            onClick={handleApplyClick}
          >
            {t("APPLY")}
          </button>
        )}
      </div>

      {showNormalize && (
        <div className="genre-normalize-bar">
          <div className="genre-normalize-inner">
            <strong>
              {t("NORMALIZE_GENRES")} ({selectedGenres.length})
            </strong>

            <div className="small text-muted mt-1">
              {selectedGenres.map((g) => g.name).join(", ")}
            </div>

            <div className="d-flex gap-2 mt-2">
              <input
                className="form-control form-control-sm"
                placeholder={t("CANONICAL_GENRE_NAME")}
                value={normalizeName}
                onChange={(e) => setNormalizeName(e.target.value)}
              />

              <button
                className="btn btn-sm btn-danger"
                disabled={!normalizeName.trim() || normalizing}
                onClick={normalizeGenres}
              >
                {normalizing ? t("APPLYING") : t("NORMALIZE")}
              </button>
            </div>

            {normalizeError && (
              <div className="text-danger small mt-1">
                {normalizeError}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default GenresPanel;
