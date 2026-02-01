import { useState } from "react";
import { t } from "../../i18n";

/* ===== Directory fields ===== */
const DIR_FIELDS = [
  { key: "artist", label: t("FIELD_ARTIST") },
  { key: "album", label: t("FIELD_ALBUM") },
  { key: "year", label: t("FIELD_YEAR") },
  { key: "genre", label: t("GENRES_TITLE") },
  { key: "compilation", label: t("COMPILATION") },
];

/* ===== Filename fields ===== */
const FILE_FIELDS = [
  { key: "track", label: "Track #" },
  { key: "title", label: t("TITLE") },
  { key: "artist", label: t("FIELD_ARTIST") },
  { key: "album", label: t("FIELD_ALBUM") },
  { key: "year", label: t("FIELD_YEAR") },
];

const SEPARATORS = [" - ", " ", "_", "."];

/* ===== Presets ===== */
const DIR_PRESETS = {
  canonical: ["artist", "album"],
  year_album: ["artist", "year", "album"],
  itunes_like: ["artist", "album"],
};

const FILE_PRESETS = {
  classic: [
    { type: "field", value: "track" },
    { type: "sep", value: " - " },
    { type: "field", value: "title" },
  ],
  artist_title: [
    { type: "field", value: "artist" },
    { type: "sep", value: " - " },
    { type: "field", value: "title" },
  ],
  title_only: [{ type: "field", value: "title" }],
  dotted: [
    { type: "field", value: "track" },
    { type: "sep", value: "." },
    { type: "field", value: "title" },
  ],
  track_artist_title: [
    { type: "field", value: "track" },
    { type: "sep", value: ". " },
    { type: "field", value: "artist" },
    { type: "sep", value: " - " },
    { type: "field", value: "title" },
  ],
};

/* ===== Sample data for preview ===== */
const SAMPLE_TRACK = {
  track: "01",
  title: "Bohemian Rhapsody",
  artist: "Queen",
  album: "A Night at the Opera",
  year: "1975",
  genre: "Rock",
  compilation: "Soundtracks",
};

function sanitize(str) {
  return str
    .replace(/[<>:"/\\|?*]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function buildFilename(layout) {
  if (!layout || layout.length === 0) return "file.mp3";

  const parts = layout.map((p) => {
    if (p.type === "field") return SAMPLE_TRACK[p.value] || "";
    if (p.type === "sep") return p.value;
    return "";
  });

  let name = sanitize(parts.join(""));
  if (name.length > 120) name = name.slice(0, 120);

  return `${name}.mp3`;
}

function buildPreviewTree(dirLayout, filename, separateCompilations) {
  const normalPath = [];
  const compPath = [];

  (dirLayout || []).forEach((k) => {
    if (k === "compilation") return;
    normalPath.push(SAMPLE_TRACK[k] || k);
  });

  if (separateCompilations) {
    compPath.push("Compilations");
    compPath.push(SAMPLE_TRACK.album);
  }

  return {
    normal: [...normalPath, filename],
    compilation: separateCompilations ? [...compPath, filename] : null,
  };
}

function renderTree(path, prefix = "") {
  return path.map((node, idx) => {
    const isLast = idx === path.length - 1;
    const line =
      prefix +
      (isLast ? "└─ " : "├─ ") +
      node;

    return (
      <div key={idx} style={{ whiteSpace: "pre", fontFamily: "monospace" }}>
        {line}
      </div>
    );
  });
}

export default function LayoutStep({
  executionPlan,
  onUpdate,
  onBack,
  onNext,
}) {
  const { paths, layout } = executionPlan;

  const sourcePath = paths?.source || "";
  const targetPath = paths?.target || "";
  const lockedByDb = paths?.locked_by_database === true;

  const dirLayout = layout.directory_layout || [];
  const fileLayout = layout.filename_layout || [];
  const separateCompilations = layout.separate_compilations ?? true;

  const [dragField, setDragField] = useState(null);
  const [dragFilePart, setDragFilePart] = useState(null);

  /* ===== Directory handlers ===== */

  const handleDirDrop = (fieldKey) => {
    if (dirLayout.includes(fieldKey)) return;
    onUpdate({
      directory_layout: [...dirLayout, fieldKey],
    });
  };

  const removeDirNode = (idx) => {
    const next = [...dirLayout];
    next.splice(idx, 1);
    onUpdate({ directory_layout: next });
  };

  /* ===== Filename handlers ===== */

  const handleFileDrop = (part) => {
    onUpdate({
      filename_layout: [...fileLayout, part],
    });
  };

  const removeFilePart = (idx) => {
    const next = [...fileLayout];
    next.splice(idx, 1);
    onUpdate({ filename_layout: next });
  };

  const hasTitle = fileLayout.some(
    (p) => p.type === "field" && p.value === "title"
  );

  const validFilename = hasTitle && fileLayout.length > 0;

  const previewFilename = buildFilename(fileLayout);

  const previewTree = buildPreviewTree(
    dirLayout,
    previewFilename,
    separateCompilations
  );

  return (
    <div className="startup-step-root">
      <h2>{t("STARTUP_STEP_LAYOUT")}</h2>

      {/* ===== IMPORTED DB BANNER ===== */}
      {lockedByDb && sourcePath && targetPath && (
        <div className="startup-info">
        <strong>📦 Imported database paths</strong>
        <div style={{ fontFamily: "monospace", marginTop: 4 }}>
          Source: {paths.source}
          <br />
          Target: {paths.target}
        </div>
        <div style={{ marginTop: 6, opacity: 0.8 }}>
          To change these paths, start a new scan instead of importing a database.
        </div>
      </div>
      )}

      <p className="startup-hint">
        Define how Pedro will build your folder structure and file names.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        {/* LEFT PANEL */}
        <div className="layout-panel">
          <h3>Directory Layout</h3>

          <div className="startup-field">
            <label>Presets</label>
            <select
              onChange={(e) => {
                const preset = DIR_PRESETS[e.target.value];
                if (preset) onUpdate({ directory_layout: [...preset] });
              }}
              value=""
            >
              <option value="">— Select preset —</option>
              <option value="canonical">Artist / Album</option>
              <option value="year_album">Artist / Year / Album</option>
              <option value="itunes_like">iTunes-like</option>
            </select>
          </div>

          <div className="layout-available">
            <strong>Available fields</strong>
            <div className="chip-row">
              {DIR_FIELDS.map((f) => (
                <div
                  key={f.key}
                  className="chip"
                  draggable
                  onDragStart={() => setDragField(f.key)}
                >
                  {f.label}
                </div>
              ))}
            </div>
          </div>

          <div
            className="layout-tree"
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => {
              if (dragField) handleDirDrop(dragField);
            }}
          >
            <strong>Directory structure</strong>

            {dirLayout.length === 0 && (
              <div className="layout-empty">Drop fields here</div>
            )}

            {dirLayout.map((node, idx) => (
              <div key={idx} className="tree-node">
                <span>{node}</span>
                <button onClick={() => removeDirNode(idx)}>✕</button>
              </div>
            ))}
          </div>

          <div className="startup-field">
            <label>
              <input
                type="checkbox"
                checked={separateCompilations}
                onChange={(e) =>
                  onUpdate({
                    separate_compilations: e.target.checked,
                  })
                }
              />{" "}
              Keep compilations in separate folder
            </label>
          </div>

          <hr />

          <h3>Filename Layout</h3>

          <div className="startup-field">
            <label>Presets</label>
            <select
              onChange={(e) => {
                const preset = FILE_PRESETS[e.target.value];
                if (preset) onUpdate({ filename_layout: [...preset] });
              }}
              value=""
            >
              <option value="">— Select preset —</option>
              <option value="classic">01 - Title</option>
              <option value="artist_title">Artist - Title</option>
              <option value="title_only">Title only</option>
              <option value="track_artist_title">
                01.Artist - Title
              </option>
              <option value="dotted">01.Title</option>
            </select>
          </div>

          <div className="layout-available">
            <strong>Fields</strong>
            <div className="chip-row">
              {FILE_FIELDS.map((f) => (
                <div
                  key={f.key}
                  className="chip"
                  draggable
                  onDragStart={() =>
                    setDragFilePart({
                      type: "field",
                      value: f.key,
                    })
                  }
                >
                  {f.label}
                </div>
              ))}
            </div>

            <strong>Separators</strong>
            <div className="chip-row">
              {SEPARATORS.map((s) => (
                <div
                  key={s}
                  className="chip sep"
                  draggable
                  onDragStart={() =>
                    setDragFilePart({
                      type: "sep",
                      value: s,
                    })
                  }
                >
                  {JSON.stringify(s)}
                </div>
              ))}
            </div>
          </div>

          <div
            className="layout-sequence"
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => {
              if (dragFilePart) handleFileDrop(dragFilePart);
            }}
          >
            <strong>Filename sequence</strong>

            <div className="sequence-row">
              {fileLayout.map((p, idx) => (
                <div key={idx} className="sequence-part">
                  <span>
                    {p.type === "field"
                      ? p.value
                      : JSON.stringify(p.value)}
                  </span>
                  <button onClick={() => removeFilePart(idx)}>
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {!hasTitle && (
            <div className="startup-error">
              Filename must include a Title field.
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div className="layout-panel">
          <h3>Preview</h3>

          <div className="layout-preview-tree">
            <strong>Normal albums</strong>
            <div className="preview-box">
              {renderTree(previewTree.normal)}
            </div>

            {separateCompilations && previewTree.compilation && (
              <>
                <strong style={{ marginTop: 12, display: "block" }}>
                  Compilations
                </strong>
                <div className="preview-box">
                  {renderTree(previewTree.compilation)}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="startup-actions">
        <button
          className="btn-secondary"
          onClick={onBack}
          disabled={lockedByDb}   // prevent going back to Paths when imported
        >
          {t("BTN_BACK")}
        </button>

        <button
          className="btn-primary"
          disabled={!validFilename || dirLayout.length === 0}
          onClick={onNext}
        >
          {t("BTN_NEXT")}
        </button>
      </div>
    </div>
  );
}
