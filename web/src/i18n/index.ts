import { computed } from "vue";

import { messages, type AppLocale, type MessageKey } from "@/i18n/messages";
import { useLocaleStore } from "@/stores/locale";

function interpolate(template: string, params?: Record<string, string | number>): string {
  if (!params) {
    return template;
  }

  return Object.entries(params).reduce(
    (result, [key, value]) => result.split(`{${key}}`).join(String(value)),
    template,
  );
}

export function translate(
  locale: AppLocale,
  fallbackLocale: AppLocale,
  key: MessageKey,
  params?: Record<string, string | number>,
) {
  const template = messages[locale][key] ?? messages[fallbackLocale][key] ?? key;
  return interpolate(template, params);
}

export function useI18n() {
  const localeStore = useLocaleStore();

  const locale = computed(() => localeStore.locale);

  function t(key: MessageKey, params?: Record<string, string | number>) {
    return translate(localeStore.locale, localeStore.fallbackLocale, key, params);
  }

  return {
    locale,
    setLocale: localeStore.setLocale,
    t,
  };
}
