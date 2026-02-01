import { useReducer, useEffect } from "react";
import { t, setLanguage, getLanguage } from "../i18n";
import pedroLogoBig from "../assets/logo.png";

import WelcomeStep from "./steps/WelcomeStep";
import ImportDbStep from "./steps/ImportDbStep";
import PathsStep from "./steps/PathsStep";
import LayoutStep from "./steps/LayoutStep";
import OptionsStep from "./steps/OptionsStep";
import ReviewStep from "./steps/ReviewStep";
import ScanStep from "./steps/ScanStep";
import DoneStep from "./steps/DoneStep";

const API_BASE = "http://127.0.0.1:8000";

const STEP_WELCOME = 0;
const STEP_IMPORT_DB = 1;
const STEP_PATHS = 2;
const STEP_LAYOUT = 3;
const STEP_OPTIONS = 4;
const STEP_REVIEW = 5;
const STEP_SCAN = 6;
const STEP_DONE = 7;

async function loadExecutionPlan() {
  try {
    const res = await fetch(`${API_BASE}/startup/load-execution-plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: "~/.config/pedro/current_plan.json",
      }),
    });

    if (!res.ok) return null;
    const data = await res.json();
    return data.plan || null;
  } catch {
    return null;
  }
}

/* ===== Initial empty execution plan ===== */

function emptyExecutionPlan() {
  const now = new Date().toISOString();

  return {
    version: 1,

    environment: {
      id: null,
      name: null,
      created_at: now,
      last_modified: now,
    },

    database: {
      db_path: null,
      mode: null,
      last_inspection: null,
    },

    paths: {
      source: "",
      target: "",
      source_inspection: null,
      target_inspection: null,
      locked_by_database: false,
    },

    layout: {
      directory_layout: null,
      filename_layout: null,
      separate_compilations: true,
    },

    options: {
      dry_run: true,
      no_overwrite: true,
      copy_mode: "rsync-like",
      max_path_length: 240,
      shorten_long_names: true,
    },

    review: {
      confirmed: false,
      confirmed_at: null,
    },
  };
}

const initialState = {
  step: STEP_WELCOME,
  startupMode: null,
  executionPlan: emptyExecutionPlan(),
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_STEP":
      return {
        ...state,
        step: Math.max(STEP_WELCOME, Math.min(STEP_DONE, action.step)),
      };

    case "NEXT_STEP":
      return {
        ...state,
        step: Math.min(STEP_DONE, state.step + 1),
      };

    case "PREV_STEP":
      return {
        ...state,
        step: Math.max(STEP_WELCOME, state.step - 1),
      };

    case "SET_MODE_AND_STEP":
      return {
        ...state,
        startupMode: action.mode,
        step: action.step,
      };

    case "UPDATE_PLAN": {
      const now = new Date().toISOString();

      const nextPlan = {
        ...state.executionPlan,
        ...action.payload,

        environment: {
          ...state.executionPlan.environment,
          ...action.payload.environment,
          last_modified: now,
        },

        database: {
          ...state.executionPlan.database,
          ...action.payload.database,
        },

        // ✅ ONLY MERGE PATHS, NEVER REPLACE WITH DEFAULTS
        paths: {
          ...state.executionPlan.paths,
          ...action.payload.paths,
        },

        layout: {
          ...state.executionPlan.layout,
          ...action.payload.layout,
        },

        options: {
          ...state.executionPlan.options,
          ...action.payload.options,
        },

        review: {
          ...state.executionPlan.review,
          ...action.payload.review,
        },
      };

      return {
        ...state,
        executionPlan: nextPlan,
      };
    }

    default:
      return state;
  }
}

export default function StartupPage({ onComplete }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { executionPlan } = state;

  /* ===== Load saved execution plan once on mount ===== */
  useEffect(() => {
    (async () => {
      const loaded = await loadExecutionPlan();
      if (loaded) {
        dispatch({
          type: "UPDATE_PLAN",
          payload: loaded,
        });
      }
    })();
  }, []);

  const steps = [
    t("STARTUP_STEP_WELCOME"),
    t("STARTUP_STEP_IMPORT_DB"),
    t("STARTUP_STEP_SOURCE"),
    t("STARTUP_STEP_LAYOUT"),
    t("STARTUP_STEP_OPTIONS"),
    t("STARTUP_STEP_REVIEW"),
    t("STARTUP_STEP_SCAN"),
    t("STARTUP_STEP_DONE"),
  ];

  return (
    <div className="startup-root">
      {/* ===== HEADER ===== */}
      <div className="startup-header">
        <img
          src={pedroLogoBig}
          alt={t("APP_NAME")}
          className="startup-logo"
        />

        <div style={{ flex: 1 }}>
          <h1>{t("APP_NAME")}</h1>
          <p className="startup-subtitle">
            {t("STARTUP_SUBTITLE")}
          </p>
        </div>

        {/* ===== LANGUAGE SWITCHER ===== */}
        <div className="startup-lang-switcher">
          <select
            value={getLanguage()}
            onChange={(e) => {
              setLanguage(e.target.value);
              window.location.reload();
            }}
          >
            <option value="en">EN</option>
            <option value="es">ES</option>
            <option value="de">DE</option>
          </select>
        </div>
      </div>

      {/* ===== BODY ===== */}
      <div className="startup-body">
        {/* ===== STEPPER ===== */}
        <div className="startup-stepper">
          {steps.map((label, index) => {
            const status =
              index < state.step
                ? "done"
                : index === state.step
                ? "active"
                : "upcoming";

            return (
              <div key={label} className={`startup-step ${status}`}>
                <div className="startup-step-index">
                  {index + 1}
                </div>
                <div className="startup-step-label">
                  {label}
                </div>
              </div>
            );
          })}
        </div>

        {/* ===== CONTENT ===== */}
        <div className="startup-content">
          {/* --- STEP 0: WELCOME --- */}
          {state.step === STEP_WELCOME && (
            <WelcomeStep
              onSetupNew={() => {
                // Reset paths when starting a new scan
                dispatch({
                  type: "UPDATE_PLAN",
                  payload: {
                    paths: {
                      source: "",
                      target: "",
                      source_inspection: null,
                      target_inspection: null,
                      locked_by_database: false,
                    },
                  },
                });

                dispatch({
                  type: "SET_MODE_AND_STEP",
                  mode: "new",
                  step: STEP_PATHS,
                });
              }}
              onImportDb={() =>
                dispatch({ type: "SET_STEP", step: STEP_IMPORT_DB })
              }
            />
          )}

          {/* --- STEP 1: IMPORT DB --- */}
          {state.step === STEP_IMPORT_DB && (
            <ImportDbStep
              onValidDb={(dbInfo) => {
                const insp = dbInfo.inspection;
                const env = dbInfo.environment;

                console.log("ACTIVATING DB WITH ENV:", env);

                dispatch({
                  type: "UPDATE_PLAN",
                  payload: {
                    database: {
                      db_path: dbInfo.db_path,
                      mode: "existing",
                      last_inspection: insp,
                    },

                    environment: {
                      name: "imported",
                    },

                    paths: {
                      source: env?.source_root || "",
                      target: env?.library_root || "",
                      source_inspection: null,
                      target_inspection: null,
                      locked_by_database: true,
                    },
                  },
                });

                dispatch({
                  type: "SET_MODE_AND_STEP",
                  mode: "import-valid",
                  step: STEP_LAYOUT,
                });
              }}

              onInvalidDb={() =>
                dispatch({
                  type: "SET_MODE_AND_STEP",
                  mode: "import-invalid",
                  step: STEP_PATHS,
                })
              }

              onBack={() =>
                dispatch({ type: "SET_STEP", step: STEP_WELCOME })
              }
            />
          )}

          {/* --- STEP 2: PATHS --- */}
          {state.step === STEP_PATHS && (
            <PathsStep
              executionPlan={executionPlan}
              onUpdate={(payload) =>
                dispatch({
                  type: "UPDATE_PLAN",
                  payload: { paths: payload },
                })
              }
              onBack={() => dispatch({ type: "PREV_STEP" })}
              onNext={() => dispatch({ type: "NEXT_STEP" })}
              
            />
          )}

          {/* --- STEP 3: LAYOUT --- */}
          {state.step === STEP_LAYOUT && (
            <LayoutStep
              executionPlan={executionPlan}
              onUpdate={(payload) =>
                dispatch({
                  type: "UPDATE_PLAN",
                  payload: { layout: payload },
                })
              }
              onBack={() => dispatch({ type: "PREV_STEP" })}
              onNext={() => dispatch({ type: "NEXT_STEP" })}
            />
          )}

          {/* --- STEP 4: OPTIONS --- */}
          {state.step === STEP_OPTIONS && (
            <OptionsStep
              options={executionPlan.options}
              onSetOptions={(opts) =>
                dispatch({
                  type: "UPDATE_PLAN",
                  payload: { options: opts },
                })
              }
              onBack={() => dispatch({ type: "PREV_STEP" })}
              onNext={() => dispatch({ type: "NEXT_STEP" })}
            />
          )}

          {/* --- STEP 5: REVIEW --- */}
          {state.step === STEP_REVIEW && (
            <ReviewStep
              executionPlan={executionPlan}
              onBack={() => dispatch({ type: "PREV_STEP" })}
              onConfirm={() => {
                dispatch({
                  type: "UPDATE_PLAN",
                  payload: {
                    review: {
                      confirmed: true,
                      confirmed_at: new Date().toISOString(),
                    },
                  },
                });

                dispatch({ type: "NEXT_STEP" });
              }}
            />
          )}

          {/* --- STEP 6: SCAN --- */}
          {state.step === STEP_SCAN && (
            <ScanStep
              executionPlan={executionPlan}
              onBack={() => dispatch({ type: "PREV_STEP" })}
              onDone={() => dispatch({ type: "NEXT_STEP" })}
            />
          )}

          {/* --- STEP 7: DONE --- */}
          {state.step === STEP_DONE && (
            <DoneStep
              executionPlan={executionPlan}
              onRestartWizard={() => {
                dispatch({ type: "SET_STEP", step: STEP_WELCOME });
              }}
              onEnterPedro={() => {
                onComplete();
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
