type AppEnv = "development" | "staging";

export interface WebAppConfig {
  env: AppEnv;
  appTitle: string;
  apiBaseUrl: string;
  defaultLocale: "de" | "en";
  fallbackLocale: "de" | "en";
  lightPrimary: string;
  darkPrimary: string;
  enableMockAuth: boolean;
  enableCustomerPortal: boolean;
  enableSubcontractorPortal: boolean;
}

function readBool(value: string | undefined, fallback: boolean): boolean {
  if (value == null) {
    return fallback;
  }
  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

export const webAppConfig: WebAppConfig = {
  env: (import.meta.env.VITE_SP_ENV ?? "development") as AppEnv,
  appTitle: import.meta.env.VITE_SP_APP_TITLE ?? "SicherPlan",
  apiBaseUrl: import.meta.env.VITE_SP_API_BASE_URL ?? "http://localhost:8000",
  defaultLocale: (import.meta.env.VITE_SP_DEFAULT_LOCALE ?? "de") as "de" | "en",
  fallbackLocale: (import.meta.env.VITE_SP_FALLBACK_LOCALE ?? "de") as "de" | "en",
  lightPrimary: `rgb(${import.meta.env.VITE_SP_LIGHT_PRIMARY ?? "40,170,170"})`,
  darkPrimary: `rgb(${import.meta.env.VITE_SP_DARK_PRIMARY ?? "35,200,205"})`,
  enableMockAuth: readBool(import.meta.env.VITE_SP_ENABLE_MOCK_AUTH, true),
  enableCustomerPortal: readBool(import.meta.env.VITE_SP_ENABLE_CUSTOMER_PORTAL, false),
  enableSubcontractorPortal: readBool(
    import.meta.env.VITE_SP_ENABLE_SUBCONTRACTOR_PORTAL,
    false,
  ),
};
