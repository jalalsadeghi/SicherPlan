import { defineStore } from "pinia";
import { loadLocaleMessages } from "@vben/locales";
import { preferences, updatePreferences } from "@vben/preferences";

import { webAppConfig } from "@/config/env";
import type { AppLocale } from "@/i18n/messages";

export const APP_LOCALE_STORAGE_KEY = "app_locale";
const STORAGE_KEY = "sicherplan-locale";

function normalizeLocale(value: string | undefined): AppLocale | null {
  switch (value) {
    case "de":
    case "de-DE":
      return "de";
    case "en":
    case "en-US":
      return "en";
    default:
      return null;
  }
}

function readStoredLocale(): AppLocale {
  const preferenceLocale = normalizeLocale(preferences.app.locale);
  if (preferenceLocale) {
    return preferenceLocale;
  }

  if (typeof window === "undefined") {
    return webAppConfig.defaultLocale;
  }

  return (
    normalizeLocale(window.localStorage.getItem(APP_LOCALE_STORAGE_KEY) ?? undefined)
    ?? normalizeLocale(window.localStorage.getItem(STORAGE_KEY) ?? undefined)
    ?? "de"
  );
}

export const useLocaleStore = defineStore("locale", {
  state: () => ({
    locale: readStoredLocale() as AppLocale,
    fallbackLocale: "de" as AppLocale,
  }),
  actions: {
    async setLocale(locale: AppLocale) {
      this.locale = locale;
      const vbenLocale = locale === "en" ? "en-US" : "de-DE";

      if (typeof window !== "undefined") {
        window.localStorage.setItem(APP_LOCALE_STORAGE_KEY, locale);
        window.localStorage.setItem(STORAGE_KEY, locale);
      }

      updatePreferences({
        app: {
          locale: vbenLocale,
        },
      });
      await loadLocaleMessages(vbenLocale);
    },
  },
});
