import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import "./index.css";
import "./css/styles.css";

import App from "./App.jsx";
import { PlaybackProvider } from "./context/PlaybackContext";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <PlaybackProvider>
      <App />
    </PlaybackProvider>
  </StrictMode>
);
