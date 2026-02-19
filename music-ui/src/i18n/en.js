// i18n/en.js
export default {
  // ===== generic =====
  LOADING: "Loading…",
  ERROR_GENERIC: "Error",
  APPLY: "Apply",
  REMOVE: "Remove",

  // ===== genres panel =====
  GENRES_TITLE: "Genres",
  GENRES_APPLIED: "Applied",
  GENRES_PARTIAL: "Partially applied",
  GENRES_AVAILABLE: "Available",
  GENRES_EMPTY_SELECTION: "Select one or more files to edit genres",

  // ===== file table =====
  FILES_FOUND: "{count} tracks found in the library",
  USE_ALPHA_FILTER: "Use the alphabetical filter to show them",
  CLEAR_FILTERS: "Clear filters",
  FILTERS: "Filters",

  ARTIST: "Artist",
  ALBUM: "Album",
  TITLE: "Title",
  PREVIEW: "Preview",
  ALL: "All",
  NUMERIC: "0–9",

  // ===== bulk edit =====
  MARK_FOR_DELETION: "Mark for deletion",

  // ===== expanded metadata =====
  ALBUM_ARTIST: "Album artist",
  YEAR: "Year",
  BPM: "BPM",
  COMPILATION: "Compilation",
  SEARCH_FAILED: "Search failed",
  ROW_APPLY_FAILED: "Failed to apply row changes",
  BULK_APPLY_FAILED: "Bulk apply failed",
  SEARCH_PLACEHOLDER: "Search…",
  FIELD_ARTIST: "Artist",
  FIELD_ALBUM: "Album",
  FIELD_TITLE: "Title",
  FIELD_ALBUM_ARTIST: "Album artist",
  FIELD_TRACK: "Track #",
  FIELD_YEAR: "Year",
  FIELD_BPM: "BPM",
  FIELD_COMPOSER: "Composer",
  FIELD_DISC: "Disc #",
  FIELD_COMPILATION: "Compilation",

  REFINE_SEARCH_HINT: "files found — please refine your search",
  SEARCHING: "Searching…",
  APPLY: "Apply",

  // ===== startup =====

  APP_NAME: "Pedro Organiza",
  STARTUP_SUBTITLE: "First-time setup",

  STARTUP_STEP_WELCOME: "Welcome",
  STARTUP_STEP_IMPORT_DB: "Import database",
  STARTUP_STEP_SOURCE: "Source",
  STARTUP_STEP_TARGET: "Target",
  STARTUP_STEP_LAYOUT: "Layout",
  STARTUP_STEP_OPTIONS: "Options",
  STARTUP_STEP_REVIEW: "Review",

  STARTUP_STEP_DONE: "Done",

  // --- Welcome ---

  STARTUP_WELCOME_TITLE: "Welcome to Pedro Organiza",

  STARTUP_WELCOME_HINT:
    "Pedro will guide you to organize your music library in a safe and controlled way.",

  STARTUP_WELCOME_BODY_1:
    "Pedro will analyze your library and build a clean, editable database.",

  STARTUP_WELCOME_BODY_2:
    "No files will be moved until you review and confirm the changes.",

  STARTUP_WELCOME_BULLET_1:
    "No files will be moved without your explicit approval.",

  STARTUP_WELCOME_BULLET_2:
    "You can review and edit all metadata before applying changes.",

  STARTUP_WELCOME_BULLET_3:
    "Duplicate detection and conflict resolution are built in.",

  STARTUP_WELCOME_BULLET_4:
    "You can import an existing database or start from scratch.",

  STARTUP_BTN_SETUP: "Set up my library",
  STARTUP_BTN_IMPORT_DB: "Import existing library database",

  // --- Import DB ---

  STARTUP_IMPORT_TITLE: "Import existing database",
  STARTUP_IMPORT_HELP:
    "Select an existing Pedro database to continue working with your library.",
  STARTUP_IMPORT_PLACEHOLDER: "path/to/your/database.sqlite",
  STARTUP_IMPORT_VALID_PATH: "Valid path",
  STARTUP_IMPORT_VALID_SQLITE: "Valid SQLite file",
  STARTUP_IMPORT_IS_PEDRO_DB: "Pedro database",
  STARTUP_IMPORT_TRACK_COUNT: "Tracks in database",
  STARTUP_IMPORT_NEEDS_MIGRATION:
    "This database needs a schema upgrade",

  STARTUP_IMPORT_HINT:
    "Select an existing Pedro database or paste the full path manually. You can inspect the database before activating it.",

  STARTUP_DB_PATH_LABEL: "Database path",
  STARTUP_DB_PATH_PLACEHOLDER: "/full/path/to/your/database.sqlite",

  STARTUP_BTN_CHOOSE_FILE: "Choose file…",
  STARTUP_BTN_INSPECT_DB: "Inspect database",
  STARTUP_BTN_ACTIVATE_DB: "Activate this database",
  STARTUP_BTN_CHANGE_DB: "Choose another database",
  STARTUP_BTN_BACK: "<<< Back",

  STARTUP_IMPORT_INSPECTION_TITLE: "Inspection result",

  STARTUP_IMPORT_VALID_PATH: "Valid path",
  STARTUP_IMPORT_VALID_SQLITE: "Valid SQLite file",
  STARTUP_IMPORT_IS_PEDRO_DB: "Pedro database",
  STARTUP_IMPORT_TRACK_COUNT: "Tracks in database",

  STARTUP_IMPORT_NEEDS_MIGRATION:
    "This database needs a schema upgrade",

  STARTUP_SOURCE_PATH_LABEL: "Source folder:",
  STARTUP_SOURCE_PATH_PLACEHOLDER: "/path/to/your/music",

  // --- Import DB Errors ---

  STARTUP_IMPORT_INVALID_EXTENSION:
    "Please select a .sqlite or .db file.",

  STARTUP_IMPORT_INVALID_PATH:
    "The selected path does not exist or is not a file.",

  STARTUP_IMPORT_INVALID_SQLITE:
    "The selected file is not a valid SQLite database.",

  STARTUP_IMPORT_INVALID_SCHEMA:
    "This file does not appear to be a Pedro database.",

  STARTUP_IMPORT_INSPECT_FAILED:
    "Failed to inspect the database.",

  STARTUP_IMPORT_ACTIVATE_FAILED:
    "Failed to activate the database.",

  // --- Source ---

  STARTUP_SOURCE_TITLE: "Choose your music folder",

  STARTUP_SOURCE_HINT:
    "Select the folder that contains your music files. Pedro will scan this directory recursively.",

  STARTUP_SOURCE_SELECTED: "Selected folder",

  STARTUP_SOURCE_NO_PATH:
    "Please choose a source folder before continuing.",

  // --- Generic buttons ---

  BTN_CONTINUE: "Continue",
  BTN_CANCEL: "Cancel",
  BTN_BACK: "Back",
  BTN_NEXT: "Next",

  STARTUP_SOURCE_INSPECTION_TITLE: "Resultado de la inspección",

  STARTUP_SOURCE_VALID_PATH: "Ruta válida",
  STARTUP_SOURCE_IS_DIRECTORY: "Es un directorio",
  STARTUP_SOURCE_IS_READABLE: "Permisos de lectura",
  STARTUP_SOURCE_AUDIO_COUNT: "Archivos de audio encontrados",

  STARTUP_SOURCE_INSPECT_FAILED:
    "No se pudo inspeccionar la carpeta de origen.",

  // Warnings (map backend codes → messages)
  STARTUP_SOURCE_WARN_NO_PATH_PROVIDED:
    "No se proporcionó ninguna ruta.",

  STARTUP_SOURCE_WARN_PATH_NOT_FOUND:
    "La ruta no existe.",

  STARTUP_SOURCE_WARN_PATH_NOT_DIRECTORY:
    "La ruta no es un directorio.",

  STARTUP_SOURCE_WARN_PERMISSION_DENIED:
    "No tienes permisos para leer esta carpeta.",

  STARTUP_SOURCE_WARN_NO_AUDIO_FILES:
    "No se encontraron archivos de audio en esta carpeta.",

  STARTUP_SOURCE_WARN_SCAN_FAILED:
    "Falló el escaneo del directorio.",
  STARTUP_STEP_PATHS: "Paths",
  // Paths step
  STARTUP_STEP_PATHS: "Paths",
  STARTUP_PATHS_HINT: "...",

  STARTUP_SOURCE_IS_DIRECTORY: "Is directory",
  STARTUP_SOURCE_IS_READABLE: "Readable",
  STARTUP_SOURCE_AUDIO_COUNT: "Audio files found",

  STARTUP_TARGET_VALID_PATH: "Valid path",
  STARTUP_TARGET_IS_DIRECTORY: "Is directory",
  STARTUP_TARGET_IS_WRITABLE: "Writable",
  STARTUP_TARGET_IS_EMPTY: "Empty directory",

  STARTUP_TARGET_PATH_LABEL: "Target folder:",
  STARTUP_TARGET_PATH_PLACEHOLDER: "/path/to/target",

  STARTUP_BTN_INSPECT_SOURCE: "Inspect source",
  STARTUP_BTN_INSPECT_TARGET: "Inspect target",
  
  // --- Target path warnings ---

  NO_PATH_PROVIDED:
    "No path was provided.",

  PATH_RESOLVE_FAILED:
    "The provided path could not be resolved.",

  INVALID_SOURCE_PATH:
    "The source path is not a valid directory.",

  TARGET_NOT_DIRECTORY:
    "The target path exists but is not a directory.",

  TARGET_PARENT_NOT_FOUND:
    "The parent directory of the target path does not exist.",

  TARGET_EQUALS_SOURCE:
    "Target directory cannot be the same as the source directory.",

  TARGET_INSIDE_SOURCE:
    "Target directory cannot be inside the source directory.",

  SOURCE_INSIDE_TARGET:
    "Source directory cannot be inside the target directory.",

  TARGET_NOT_WRITABLE:
    "Target directory is not writable. Please check permissions.",

  CANNOT_LIST_TARGET:
    "Cannot read the contents of the target directory.",

  TARGET_NOT_EMPTY:
  "Target directory is not empty. Existing files will not be modified, but new files may be written here.",
  STARTUP_LAYOUT_AVAILABLE_FIELDS: "Available fields",
  STARTUP_LAYOUT_PRESETS: "Export presets",
  STARTUP_LAYOUT_BUILDER: "Layout builder",
  STARTUP_LAYOUT_HINT:
    "Build the folder structure by adding fields as children. This defines how files will be organized on disk.",
  STARTUP_LAYOUT_PREVIEW: "Preview",

  REVIEW_HINT: "Review the complete operation before starting the scan. This is the last step before any changes are made.",
  REVIEW_SECTION_MODE: "Operation mode",
  REVIEW_SECTION_DATABASE: "Database",
  REVIEW_SECTION_PATHS: "Paths",
  REVIEW_SECTION_LAYOUT: "Layout",
  REVIEW_SECTION_OPTIONS: "Scan options",
  REVIEW_SECTION_WARNINGS: "Warnings",
  REVIEW_SECTION_JSON: "Raw execution plan (JSON)",

  REVIEW_MODE_EXISTING_DB: "Import existing database", 
  REVIEW_MODE_NEW_SCAN: "Create new database by scanning a directory",

  REVIEW_DB_PATH: "Database file",

  REVIEW_SOURCE: "Source directory",
  REVIEW_TARGET: "Canonical library directory",

  REVIEW_PATHS_LOCKED: "These paths come from the imported database and cannot be changed in this run.",

  REVIEW_DIR_LAYOUT: "Directory layout",
  REVIEW_FILE_LAYOUT: "Filename layout",
  REVIEW_SEPARATE_COMP: "Separate compilations",

  REVIEW_DRY_RUN: "Dry run (no disk writes)",
  REVIEW_NO_OVERWRITE: "Do not overwrite existing files",
  REVIEW_COPY_MODE: "Copy mode",
  REVIEW_MAX_PATH: "Maximum path length",
  REVIEW_SHORTEN_NAMES: "Shorten long names",

  REVIEW_WARN_NO_SOURCE: "No source directory is defined.",
  REVIEW_WARN_NO_TARGET: "No target directory is defined.",
  REVIEW_WARN_NO_DIR_LAYOUT: "No directory layout has been defined.",
  REVIEW_WARN_NO_FILE_LAYOUT: "No filename layout has been defined.",

  BTN_SAVE_PRESET: "Save as preset",
  BTN_PROCEED_TO_SCAN: "Proceed to scan",

  PRESET_COMING_SOON: "Preset support will be added in a future version.",

  YES: "Yes",
  NO: "No",

  STARTUP_STEP_SCAN: "Scan",
  STARTUP_SCAN_HINT: "Pedro is ready to scan your library using the configuration below.",

  STARTUP_SCAN_DB_LABEL: "Database",
  STARTUP_SCAN_SOURCE_LABEL: "Source folder",
  STARTUP_SCAN_TARGET_LABEL: "Target library",
  STARTUP_SCAN_MODE_LABEL: "Mode",
  STARTUP_SCAN_OPTIONS_LABEL: "Scan options",

  STARTUP_SCAN_MODE_NEW: "New database (full scan)",
  STARTUP_SCAN_MODE_EXISTING: "Existing database (incremental scan)",

  STARTUP_SCAN_WITH_FINGERPRINT: "Audio fingerprinting",
  STARTUP_SCAN_SEARCH_COVERS: "Search album covers",
  STARTUP_SCAN_NO_OVERWRITE: "Do not overwrite existing data",

  STARTUP_SCAN_READY: "Ready to start scanning.",
  STARTUP_SCAN_RUNNING: "Scanning in progress…",
  STARTUP_SCAN_RUNNING_HINT: "This may take a long time depending on the size of your library.",

  STARTUP_SCAN_SUCCESS: "Scan completed successfully.",

  STARTUP_BTN_RUN_SCAN: "Run scan",
  STARTUP_BTN_RETRY_SCAN: "Retry scan",

  STARTUP_SCAN_FAILED: "Scan failed. Please check the error details.",
  STARTUP_SCAN_FAILED_HINT: "Please check the error details below and try again.",

  SRC_NOT_FOUND: "Source folder not found.",
  LIB_NOT_FOUND: "Target folder not found.",
  SCAN_ALREADY_RUNNING: "A scan is already running.",
  DRY_RUN_NOT_SUPPORTED_YET: "Dry-run is not supported yet.",
  STARTUP_SCAN_INVALID_PLAN: "Invalid execution plan. Please go back and review your settings.",

  // ===== DoneStep =====

  STARTUP_STEP_DONE: "Done",

  STARTUP_DONE_HINT: "The scan has finished successfully. You can now enter Pedro or export this run summary for later reference.",

  STARTUP_DONE_DB_LABEL: "Database",
  STARTUP_DONE_SOURCE_LABEL: "Source folder",
  STARTUP_DONE_TARGET_LABEL: "Target library",
  STARTUP_DONE_MODE_LABEL: "Mode",
  STARTUP_DONE_MODE_NEW: "New database",
  STARTUP_DONE_MODE_EXISTING: "Existing database",

  STARTUP_DONE_OPTIONS_LABEL: "Scan options",

  STARTUP_DONE_EXPORT_TITLE: "Export run summary",
  STARTUP_DONE_EXPORT_HINT: "You can download a copy of this configuration and results for future auditing or documentation.",

  STARTUP_DONE_EXPORT_JSON: "Download JSON",
  STARTUP_DONE_EXPORT_XML: "Download XML",

  STARTUP_DONE_RESTART: "Restart wizard",
  STARTUP_DONE_ENTER_PEDRO: "Enter Pedro",
  APPLY_DELETIONS: "Apply deletions",
  LANDING_TITLE: "Pedro Organiza",
  LANDING_SUBTITLE: "A personal music library manager",
  LANDING_CHECKING_ENV: "Checking environment...",
  LANDING_USING_DB: "Using existing database",
  LANDING_ENTER_WIZARD: "Enter startup wizard",
  LANDING_ENTER_DIRECT: "Enter directly",

  BTN_PROCEED_TO_SCAN: "Proceed to scan",
  BTN_SAVE_PRESET: "Save preset",
  BTN_LOAD_PRESET: "Load preset",
  BTN_BACK: "Back",
  BTN_NEXT: "Next",
  BTN_FINISH: "Finish",
  BTN_CANCEL: "Cancel",

  WIZARD_TITLE: "Startup Wizard",
  WIZARD_STEP_WELCOME: "Welcome",
  WIZARD_STEP_DB: "Database",
  WIZARD_STEP_PATHS: "Paths",
  WIZARD_STEP_OPTIONS: "Options",
  WIZARD_STEP_REVIEW: "Review",
  WIZARD_STEP_SCAN: "Scan",

  WIZARD_WELCOME_TITLE: "Welcome to Pedro Organiza",
  WIZARD_WELCOME_SUBTITLE: "This wizard will guide you through the initial setup",

  REVIEW_DB_PATH: "Database path",
  REVIEW_DIR_LAYOUT: "Directory layout",
  REVIEW_COPY_MODE: "Copy mode",
  REVIEW_OPTIONS: "Options",
  REVIEW_READY: "Ready to start",

  DRY_RUN_NOT_SUPPORTED_YET: "Dry-run not supported yet",
  LIB_NOT_FOUND: "Library directory not found",
  SRC_NOT_FOUND: "Source directory not found",
  NO: "No",
  YES: "Yes",

  SCAN_IN_PROGRESS: "Scan in progress...",
  SCAN_COMPLETED: "Scan completed successfully",
  SCAN_FAILED: "Scan failed",
  SCAN_ABORTED: "Scan aborted",

  APPLY_DELETIONS: "Apply deletions",
  APPLY_DELETIONS_WARNING: "This operation will permanently delete files",

  PRESET_COMING_SOON: "Presets coming soon",
  PRESET_NAME: "Preset name",
  PRESET_SAVED: "Preset saved",

  ERROR_GENERIC: "An unexpected error occurred",
  ERROR_INVALID_PLAN: "Invalid startup plan",
  ERROR_CANNOT_SAVE: "Cannot save configuration",
  ERROR_CANNOT_LOAD: "Cannot load configuration",

  NO_RESULTS: "No files match the current filters",
  SEARCHING: "Searching...",
  LOADING: "Loading...",

  ITEMS_SELECTED: "items selected",
  CLEAR_SELECTION: "Clear selection",

  BULK_APPLY: "Apply bulk",
  BULK_MARK_DELETE: "Mark for deletion",

  REFINE_SEARCH_HINT: "Refine your search to display files",
  TAXONOMY_LISTED: "Taxonomy listed",
  TAXONOMY_NORMALIZED: "Taxonomy normalized",
  EMPTY_TAXONOMY_PURGED: "Empty taxonomy purged",
  GENRES_LISTED: "Genres listed",
  GENRES_SEARCH_PLACEHOLDER: "Search genres…",
  PEDRO_DB_OK: "Pedro database detected OK and is ready to use.",
  FILES_COUNT: "files",
  GENRES_COUNT: "genres",
  FOUND_AUDIO_FILES: "Found audio files",
  NORMALIZE_GENRES: "Normalize genres",
  CANONICAL_GENRE_NAME: "Canonical genre name",
  FIELD_IS_COMPILATION: "Part of compilation",
  PENDING_CHANGES: "pending changes",
  FILES_MARKED_FOR_DELETION: "files marked for deletion",
  CONFIRM_DELETION_WARNING: "I understand that this operation is irreversible",
  APPLY_PENDING_OPERATIONS: "Apply pending operations",

  DOCTOR_SUMMARY_OK: "System is healthy.",
  DOCTOR_SUMMARY_WARN: "System has warnings.",
  DOCTOR_SUMMARY_FAIL: "System has critical issues.",
  DOCTOR_REPORT_SAVED: "Doctor report saved to:",
  DOCTOR_RUNNING: "Running system diagnostics...",
  DOCTOR_COMPLETED: "Diagnostics completed.",
  DOCTOR_CHECK_DB_SCHEMA: "Database schema version",
  DOCTOR_CHECK_DB_PATH: "Database path validity",
  DOCTOR_CHECK_DB_LOCK: "Database lock state",
  DOCTOR_CHECK_DEPENDENCIES: "Optional dependencies",
  DOCTOR_CHECK_REPORT_COUNT: "Doctor report history",
  DOCTOR_DB_SCHEMA_OK: "Schema version is up to date.",
  DOCTOR_DB_SCHEMA_OLD: "Schema upgrade available.",
  DOCTOR_DB_LOCK_DETECTED: "Database appears to be locked.",
  DOCTOR_DEP_FFMPEG_MISSING: "ffmpeg not found (optional).",
  DOCTOR_REPORTS_MANY: "Many doctor reports detected.",
  DOCTOR_ADVICE_RUN_MIGRATE: "Run 'pedro migrate' to update schema.",
  DOCTOR_ADVICE_INSTALL_FFMPEG: "Install ffmpeg for fingerprinting support.",
  DOCTOR_ADVICE_PRUNE_REPORTS: "Consider pruning older doctor reports.",


};
