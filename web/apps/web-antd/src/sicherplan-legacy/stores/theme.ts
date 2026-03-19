import { defineStore } from "pinia";

import type { ThemeMode } from "@/theme/tokens";

const STORAGE_KEY = "sicherplan-theme-mode";

function readStoredMode(): ThemeMode {
  if (typeof window === "undefined") {
    return "light";
  }

  return window.localStorage.getItem(STORAGE_KEY) === "dark" ? "dark" : "light";
}

export const useThemeStore = defineStore("theme", {
  state: () => ({
    mode: readStoredMode() as ThemeMode,
  }),
  actions: {
    setMode(mode: ThemeMode) {
      this.mode = mode;

      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, mode);
      }
    },
    toggleMode() {
      this.setMode(this.mode === "light" ? "dark" : "light");
    },
  },
});
