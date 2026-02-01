// i18n/de.js
export default {
  // ===== generic =====
  LOADING: "Laden…",
  ERROR_GENERIC: "Fehler",
  APPLY: "Anwenden",
  REMOVE: "Entfernen",

  // ===== genres panel =====
  GENRES_TITLE: "Genres",
  GENRES_APPLIED: "Angewendet",
  GENRES_PARTIAL: "Teilweise angewendet",
  GENRES_AVAILABLE: "Verfügbar",
  GENRES_EMPTY_SELECTION: "Wähle eine oder mehrere Dateien aus, um Genres zu bearbeiten",

  // ===== file table =====
  FILES_FOUND: "{count} Titel in der Bibliothek gefunden",
  USE_ALPHA_FILTER: "Verwende den alphabetischen Filter",
  CLEAR_FILTERS: "Filter löschen",
  FILTERS: "Filter",

  ARTIST: "Interpret",
  ALBUM: "Album",
  TITLE: "Titel",
  PREVIEW: "Vorschau",
  ALL: "Alle",
  NUMERIC: "0–9",

  // ===== bulk edit =====
  MARK_FOR_DELETION: "Zum Löschen markieren",

  // ===== expanded metadata =====
  ALBUM_ARTIST: "Album-Interpret",
  YEAR: "Jahr",
  BPM: "BPM",
  COMPILATION: "Kompilation",
  SEARCH_FAILED: "Suche fehlgeschlagen",
  ROW_APPLY_FAILED: "Zeilenänderung fehlgeschlagen",
  BULK_APPLY_FAILED: "Sammeländerung fehlgeschlagen",
  SEARCH_PLACEHOLDER: "Suchen…",
  FIELD_ARTIST: "Interpret",
  FIELD_ALBUM: "Album",
  FIELD_TITLE: "Titel",
  FIELD_ALBUM_ARTIST: "Album-Interpret",
  FIELD_TRACK: "Track #",
  FIELD_YEAR: "Jahr",
  FIELD_BPM: "BPM",
  FIELD_COMPOSER: "Komponist",
  FIELD_DISC: "Disc #",
  FIELD_COMPILATION: "Kompilation",

  REFINE_SEARCH_HINT: "Dateien gefunden — bitte Suche verfeinern",
  SEARCHING: "Suche…",
  APPLY: "Anwenden",

  // ===== startup =====

  APP_NAME: "Pedro Organiza",
  STARTUP_SUBTITLE: "Ersteinrichtung",

  STARTUP_STEP_WELCOME: "Willkommen",
  STARTUP_STEP_IMPORT_DB: "Datenbank importieren",
  STARTUP_STEP_SOURCE: "Quelle",
  STARTUP_STEP_TARGET: "Ziel",
  STARTUP_STEP_LAYOUT: "Layout",
  STARTUP_STEP_OPTIONS: "Optionen",
  STARTUP_STEP_REVIEW: "Überprüfung",
  STARTUP_STEP_SCAN: "Scan",
  STARTUP_STEP_DONE: "Fertig",

  // --- Welcome ---

  STARTUP_WELCOME_TITLE: "Willkommen bei Pedro Organiza",

  STARTUP_WELCOME_HINT:
    "Pedro hilft dir, deine Musikbibliothek sicher und kontrolliert zu organisieren.",

  STARTUP_WELCOME_BODY_1:
    "Pedro analysiert deine Bibliothek und erstellt eine saubere, bearbeitbare Datenbank.",

  STARTUP_WELCOME_BODY_2:
    "Keine Dateien werden verschoben, bevor du die Änderungen bestätigst.",

  STARTUP_WELCOME_BULLET_1:
    "Keine Dateien ohne deine ausdrückliche Zustimmung.",

  STARTUP_WELCOME_BULLET_2:
    "Du kannst alle Metadaten vor dem Anwenden überprüfen und bearbeiten.",

  STARTUP_WELCOME_BULLET_3:
    "Duplikaterkennung und Konfliktlösung sind integriert.",

  STARTUP_WELCOME_BULLET_4:
    "Du kannst eine bestehende Datenbank importieren oder neu beginnen.",

  STARTUP_BTN_SETUP: "Meine Bibliothek einrichten",
  STARTUP_BTN_IMPORT_DB: "Bestehende Bibliotheksdatenbank importieren",

  // --- Import DB ---

  STARTUP_IMPORT_TITLE: "Bestehende Datenbank importieren",
  STARTUP_IMPORT_HELP:
    "Wähle eine bestehende Pedro-Datenbank, um weiterzuarbeiten.",
  STARTUP_IMPORT_PLACEHOLDER: "pfad/zu/deiner/datenbank.sqlite",
  STARTUP_IMPORT_VALID_PATH: "Gültiger Pfad",
  STARTUP_IMPORT_VALID_SQLITE: "Gültige SQLite-Datei",
  STARTUP_IMPORT_IS_PEDRO_DB: "Pedro-Datenbank",
  STARTUP_IMPORT_TRACK_COUNT: "Titel in der Datenbank",
  STARTUP_IMPORT_NEEDS_MIGRATION:
    "Diese Datenbank benötigt ein Schema-Upgrade",

  STARTUP_IMPORT_HINT:
    "Wähle eine bestehende Pedro-Datenbank oder füge den vollständigen Pfad manuell ein. Du kannst die Datenbank vor der Aktivierung prüfen.",

  STARTUP_DB_PATH_LABEL: "Datenbankpfad",
  STARTUP_DB_PATH_PLACEHOLDER: "/vollständiger/pfad/zur/datenbank.sqlite",

  STARTUP_BTN_CHOOSE_FILE: "Datei wählen…",
  STARTUP_BTN_INSPECT_DB: "Datenbank prüfen",
  STARTUP_BTN_ACTIVATE_DB: "Diese Datenbank aktivieren",
  STARTUP_BTN_CHANGE_DB: "Andere Datenbank wählen",
  STARTUP_BTN_BACK: "<<< Zurück",

  STARTUP_IMPORT_INSPECTION_TITLE: "Prüfergebnis",

  STARTUP_IMPORT_VALID_PATH: "Gültiger Pfad",
  STARTUP_IMPORT_VALID_SQLITE: "Gültige SQLite-Datei",
  STARTUP_IMPORT_IS_PEDRO_DB: "Pedro-Datenbank",
  STARTUP_IMPORT_TRACK_COUNT: "Titel in der Datenbank",

  STARTUP_IMPORT_NEEDS_MIGRATION:
    "Diese Datenbank benötigt ein Schema-Upgrade",

  STARTUP_SOURCE_PATH_LABEL: "Quellordner:",
  STARTUP_SOURCE_PATH_PLACEHOLDER: "/pfad/zu/deiner/musik",

  // --- Import DB Errors ---

  STARTUP_IMPORT_INVALID_EXTENSION:
    "Bitte wähle eine .sqlite- oder .db-Datei.",

  STARTUP_IMPORT_INVALID_PATH:
    "Der ausgewählte Pfad existiert nicht oder ist keine Datei.",

  STARTUP_IMPORT_INVALID_SQLITE:
    "Die ausgewählte Datei ist keine gültige SQLite-Datenbank.",

  STARTUP_IMPORT_INVALID_SCHEMA:
    "Diese Datei scheint keine Pedro-Datenbank zu sein.",

  STARTUP_IMPORT_INSPECT_FAILED:
    "Datenbankprüfung fehlgeschlagen.",

  STARTUP_IMPORT_ACTIVATE_FAILED:
    "Datenbank konnte nicht aktiviert werden.",

  // --- Source ---

  STARTUP_SOURCE_TITLE: "Musikordner auswählen",

  STARTUP_SOURCE_HINT:
    "Wähle den Ordner mit deinen Musikdateien. Pedro durchsucht dieses Verzeichnis rekursiv.",

  STARTUP_SOURCE_SELECTED: "Ausgewählter Ordner",

  STARTUP_SOURCE_NO_PATH:
    "Bitte wähle einen Quellordner, bevor du fortfährst.",

  // --- Generic buttons ---

  BTN_CONTINUE: "Weiter",
  BTN_CANCEL: "Abbrechen",
  BTN_BACK: "Zurück",
  BTN_NEXT: "Weiter",

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
  // --- Zielordner-Warnungen ---

NO_PATH_PROVIDED:
  "Es wurde kein Pfad angegeben.",

PATH_RESOLVE_FAILED:
  "Der angegebene Pfad konnte nicht aufgelöst werden.",

INVALID_SOURCE_PATH:
  "Der Quellpfad ist kein gültiges Verzeichnis.",

TARGET_NOT_DIRECTORY:
  "Der Zielpfad existiert, ist aber kein Verzeichnis.",

TARGET_PARENT_NOT_FOUND:
  "Das übergeordnete Verzeichnis des Zielpfads existiert nicht.",

TARGET_EQUALS_SOURCE:
  "Zielverzeichnis darf nicht identisch mit dem Quellverzeichnis sein.",

TARGET_INSIDE_SOURCE:
  "Das Zielverzeichnis darf nicht innerhalb des Quellverzeichnisses liegen.",

SOURCE_INSIDE_TARGET:
  "Das Quellverzeichnis darf nicht innerhalb des Zielverzeichnisses liegen.",

TARGET_NOT_WRITABLE:
  "Das Zielverzeichnis ist nicht beschreibbar. Bitte Berechtigungen prüfen.",

CANNOT_LIST_TARGET:
  "Der Inhalt des Zielverzeichnisses konnte nicht gelesen werden.",

TARGET_NOT_EMPTY:
  "Das Zielverzeichnis ist nicht leer. Vorhandene Dateien werden nicht verändert, aber neue Dateien können hier geschrieben werden.",
STARTUP_LAYOUT_AVAILABLE_FIELDS: "Available fields",
STARTUP_LAYOUT_PRESETS: "Export presets",
STARTUP_LAYOUT_BUILDER: "Layout builder",
STARTUP_LAYOUT_HINT:
  "Build the folder structure by adding fields as children. This defines how files will be organized on disk.",
STARTUP_LAYOUT_PREVIEW: "Preview",
};
