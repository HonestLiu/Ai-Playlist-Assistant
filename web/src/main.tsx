import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "@/App";
import "@/index.css";
import { applyTheme, useThemeStore } from "@/stores/theme";

// 首屏立刻套用主题，避免闪白
applyTheme(useThemeStore.getState().theme);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
