import { defineStore } from "pinia";

import { webAppConfig } from "@/config/env";
import type { AppLocale } from "@/i18n/messages";

const STORAGE_KEY = "sicherplan-locale";

function readStoredLocale(): AppLocale {
  if (typeof window === "undefined") {
    return webAppConfig.defaultLocale;
  }

  const value = window.localStorage.getItem(STORAGE_KEY);
  return value === "en" ? "en" : "de";
}

export const useLocaleStore = defineStore("locale", {
  state: () => ({
    locale: readStoredLocale() as AppLocale,
    fallbackLocale: webAppConfig.fallbackLocale as AppLocale,
  }),
  actions: {
    setLocale(locale: AppLocale) {
      this.locale = locale;

      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, locale);
      }
    },
  },
});
