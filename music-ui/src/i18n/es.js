// i18n/es.js
export default {
  // ===== generic =====
  LOADING: "Cargando…",
  ERROR_GENERIC: "Error",
  APPLY: "Aplicar",
  REMOVE: "Eliminar",

  // ===== genres panel =====
  GENRES_TITLE: "Géneros",
  GENRES_APPLIED: "Aplicados",
  GENRES_PARTIAL: "Parcialmente aplicados",
  GENRES_AVAILABLE: "Disponibles",
  GENRES_EMPTY_SELECTION: "Selecciona uno o más archivos para editar géneros",

  // ===== file table =====
  FILES_FOUND: "{count} pistas encontradas en la biblioteca",
  USE_ALPHA_FILTER: "Usa el filtro alfabético para mostrarlas",
  CLEAR_FILTERS: "Limpiar filtros",
  FILTERS: "Filtros",

  ARTIST: "Artista",
  ALBUM: "Álbum",
  TITLE: "Título",
  PREVIEW: "Vista previa",
  ALL: "Todos",
  NUMERIC: "0–9",

  // ===== bulk edit =====
  MARK_FOR_DELETION: "Marcar para eliminación",

  // ===== expanded metadata =====
  ALBUM_ARTIST: "Artista del álbum",
  YEAR: "Año",
  BPM: "BPM",
  COMPILATION: "Compilación",
  SEARCH_FAILED: "Búsqueda fallida",
  ROW_APPLY_FAILED: "Fallo al aplicar cambios",
  BULK_APPLY_FAILED: "Cambios en bloque fallidos",
  SEARCH_PLACEHOLDER: "Buscar…",
  FIELD_ARTIST: "Artista",
  FIELD_ALBUM: "Album",
  FIELD_TITLE: "Título",
  FIELD_ALBUM_ARTIST: "Artista del álbum",
  FIELD_TRACK: "Track #",
  FIELD_YEAR: "Año",
  FIELD_BPM: "BPM",
  FIELD_COMPOSER: "Compositor",
  FIELD_DISC: "Disco #",
  FIELD_COMPILATION: "Compilación",
  
  REFINE_SEARCH_HINT: "archivos encontrados — por favor, refine su búsqueda",
  SEARCHING: "Buscando…",
  APPLY: "Aplicar",
  
    // ===== startup =====

  APP_NAME: "Pedro Organiza",
  STARTUP_SUBTITLE: "Configuración inicial",

  STARTUP_STEP_WELCOME: "Bienvenida",
  STARTUP_STEP_IMPORT_DB: "Importar base de datos",
  STARTUP_STEP_SOURCE: "Origen",
  STARTUP_STEP_TARGET: "Destino",
  STARTUP_STEP_LAYOUT: "Diseño",
  STARTUP_STEP_OPTIONS: "Opciones",
  STARTUP_STEP_REVIEW: "Revisión",
  STARTUP_STEP_SCAN: "Escaneo",
  STARTUP_STEP_DONE: "Finalizado",

  // --- Welcome ---

  STARTUP_WELCOME_TITLE: "Bienvenido a Pedro Organiza",

  STARTUP_WELCOME_HINT:
    "Pedro te guiará para organizar tu biblioteca de música de forma segura y controlada.",

  STARTUP_WELCOME_BODY_1:
    "Pedro analizará tu biblioteca y construirá una base de datos limpia y editable.",

  STARTUP_WELCOME_BODY_2:
    "Ningún archivo se moverá hasta que revises y confirmes los cambios.",

  STARTUP_WELCOME_BULLET_1:
    "No se moverán archivos sin tu aprobación explícita.",

  STARTUP_WELCOME_BULLET_2:
    "Puedes revisar y editar todos los metadatos antes de aplicar cambios.",

  STARTUP_WELCOME_BULLET_3:
    "Detección de duplicados y resolución de conflictos incluidos.",

  STARTUP_WELCOME_BULLET_4:
    "Puedes importar una base de datos existente o empezar desde cero.",

  STARTUP_BTN_SETUP: "Configuración inicial de mi biblioteca",
  STARTUP_BTN_IMPORT_DB: "Importar base de datos con datos de biblioteca existente",

  // --- Import DB ---

  STARTUP_IMPORT_TITLE: "Importar base de datos existente",
  STARTUP_IMPORT_HELP: "Selecciona una base de datos existente de Pedro para continuar trabajando con tu biblioteca.",
  STARTUP_IMPORT_PLACEHOLDER: "destino/a/tu/base_de_datos.sqlite",
  STARTUP_IMPORT_VALID_PATH: "Ruta válida",
  STARTUP_IMPORT_VALID_SQLITE: "Archivo SQLite válido",
  STARTUP_IMPORT_IS_PEDRO_DB: "Base de datos de Pedro",
  STARTUP_IMPORT_TRACK_COUNT: "Pistas en la base de datos",
  STARTUP_IMPORT_NEEDS_MIGRATION: "Esta base de datos necesita una actualización de esquema",

  STARTUP_IMPORT_HINT:
    "Selecciona una base de datos existente de Pedro o pega la ruta completa manualmente. Puedes inspeccionar la base de datos antes de activarla.",

  STARTUP_DB_PATH_LABEL: "Ruta de la base de datos",
  STARTUP_DB_PATH_PLACEHOLDER: "/ruta/completa/a/tu/base_de_datos.sqlite",

  STARTUP_BTN_CHOOSE_FILE: "Elegir archivo…",
  STARTUP_BTN_INSPECT_DB: "Inspeccionar base de datos",
  STARTUP_BTN_ACTIVATE_DB: "Activar esta base de datos",
  STARTUP_BTN_CHANGE_DB: "Elegir otra base de datos",
  STARTUP_BTN_BACK: "<<< Atrás",

  STARTUP_IMPORT_INSPECTION_TITLE: "Resultado de la inspección",

  STARTUP_IMPORT_VALID_PATH: "Ruta válida",
  STARTUP_IMPORT_VALID_SQLITE: "Archivo SQLite válido",
  STARTUP_IMPORT_IS_PEDRO_DB: "Base de datos de Pedro",
  STARTUP_IMPORT_TRACK_COUNT: "Pistas en la base de datos",

  STARTUP_IMPORT_NEEDS_MIGRATION:
    "Esta base de datos necesita una actualización de esquema",
  
  STARTUP_SOURCE_PATH_LABEL: "Carpeta de origen:",
  STARTUP_SOURCE_PATH_PLACEHOLDER: "/ruta/a/tu/musica",
  // --- Import DB Errors ---

  STARTUP_IMPORT_INVALID_EXTENSION:
    "Por favor selecciona un archivo .sqlite o .db.",

  STARTUP_IMPORT_INVALID_PATH:
    "La ruta seleccionada no existe o no es un archivo.",

  STARTUP_IMPORT_INVALID_SQLITE:
    "El archivo seleccionado no es una base de datos SQLite válida.",

  STARTUP_IMPORT_INVALID_SCHEMA:
    "Este archivo no parece ser una base de datos de Pedro.",

  STARTUP_IMPORT_INSPECT_FAILED:
    "No se pudo inspeccionar la base de datos.",

  STARTUP_IMPORT_ACTIVATE_FAILED:
    "No se pudo activar la base de datos.",

  // --- Source ---

  STARTUP_SOURCE_TITLE: "Elige tu carpeta de música",

  STARTUP_SOURCE_HINT:
    "Selecciona la carpeta que contiene tus archivos de música. Pedro escaneará este directorio recursivamente.",

  STARTUP_SOURCE_SELECTED: "Carpeta seleccionada",

  STARTUP_SOURCE_NO_PATH:
    "Por favor selecciona una carpeta de origen antes de continuar.",

  // --- Generic buttons ---

  BTN_CONTINUE: "Continuar",
  BTN_CANCEL: "Cancelar",
  BTN_BACK: "Atrás",
  BTN_NEXT: "Siguiente",

  STARTUP_BTN_INSPECT_SOURCE: "Inspeccionar carpeta",

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
  // --- Advertencias de carpeta de destino ---

  NO_PATH_PROVIDED:
    "No se proporcionó ninguna ruta.",

  PATH_RESOLVE_FAILED:
    "No se pudo resolver la ruta proporcionada.",

  INVALID_SOURCE_PATH:
    "La ruta de origen no es un directorio válido.",

  TARGET_NOT_DIRECTORY:
    "La ruta de destino existe pero no es un directorio.",

  TARGET_PARENT_NOT_FOUND:
    "La carpeta padre de la ruta de destino no existe.",

  TARGET_EQUALS_SOURCE:
    "La carpeta de destino no puede ser la misma que la carpeta de origen.",

  TARGET_INSIDE_SOURCE:
    "La carpeta de destino no puede estar dentro de la carpeta de origen.",

  SOURCE_INSIDE_TARGET:
    "La carpeta de origen no puede estar dentro de la carpeta de destino.",

  TARGET_NOT_WRITABLE:
    "La carpeta de destino no es escribible. Revisa los permisos.",

  CANNOT_LIST_TARGET:
    "No se pudo leer el contenido de la carpeta de destino.",

  TARGET_NOT_EMPTY:
    "La carpeta de destino no está vacía. Los archivos existentes no se modificarán, pero se escribirán nuevos archivos aquí.",

  STARTUP_LAYOUT_AVAILABLE_FIELDS: "Available fields",
  STARTUP_LAYOUT_PRESETS: "Export presets",
  STARTUP_LAYOUT_BUILDER: "Layout builder",
  STARTUP_LAYOUT_HINT:
    "Build the folder structure by adding fields as children. This defines how files will be organized on disk.",
  STARTUP_LAYOUT_PREVIEW: "Preview",
};
