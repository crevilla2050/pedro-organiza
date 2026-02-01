// i18n/index.js

import es from "./es";
import en from "./en";
import de from "./de";

// -------------------------------------------------
// Language selection
// -------------------------------------------------

// Default language: Spanish (as you chose)
let LANG = localStorage.getItem("lang") || "es";

const DICTS = {
  es,
  en,
  de,
};

// -------------------------------------------------
// Dev-only key consistency check
// -------------------------------------------------

if (process.env.NODE_ENV !== "production") {
  const baseKeys = Object.keys(es).sort();

  for (const [lang, dict] of Object.entries(DICTS)) {
    const keys = Object.keys(dict).sort();

    const missing = baseKeys.filter((k) => !keys.includes(k));
    const extra = keys.filter((k) => !baseKeys.includes(k));

    if (missing.length || extra.length) {
      console.warn(`[i18n] Key mismatch in '${lang}'`);

      if (missing.length) {
        console.warn("  Missing keys:", missing);
      }

      if (extra.length) {
        console.warn("  Extra keys:", extra);
      }
    }
  }
}

// -------------------------------------------------
// Translation function
// -------------------------------------------------

export function t(key, params = {}) {
  const dict = DICTS[LANG] || DICTS.en;
  let str = dict[key];

  // Fallback: show the key itself if missing
  if (str === undefined) {
    if (process.env.NODE_ENV !== "production") {
      console.warn(`[i18n] Missing key '${key}' in language '${LANG}'`);
    }
    str = key;
  }

  // Simple {param} replacement
  for (const [k, v] of Object.entries(params)) {
    str = str.replaceAll(`{${k}}`, String(v));
  }

  return str;
}

// -------------------------------------------------
// Language control API (for future switcher)
// -------------------------------------------------

export function getLanguage() {
  return LANG;
}

export function setLanguage(lang) {
  if (!DICTS[lang]) {
    console.warn(`[i18n] Unknown language '${lang}', keeping '${LANG}'`);
    return;
  }

  LANG = lang;
  localStorage.setItem("lang", lang);
}
