class AppConfig {
  const AppConfig({
    required this.env,
    required this.apiBaseUrl,
    required this.defaultLocale,
    required this.fallbackLocale,
    required this.lightPrimary,
    required this.darkPrimary,
    required this.enableMockAuth,
    required this.enableOfflineCache,
  });

  final String env;
  final String apiBaseUrl;
  final String defaultLocale;
  final String fallbackLocale;
  final String lightPrimary;
  final String darkPrimary;
  final bool enableMockAuth;
  final bool enableOfflineCache;

  static const AppConfig current = AppConfig(
    env: String.fromEnvironment("SP_ENV", defaultValue: "development"),
    apiBaseUrl: String.fromEnvironment(
      "SP_API_BASE_URL",
      defaultValue: "http://10.0.2.2:8000",
    ),
    defaultLocale: String.fromEnvironment(
      "SP_DEFAULT_LOCALE",
      defaultValue: "de",
    ),
    fallbackLocale: String.fromEnvironment(
      "SP_FALLBACK_LOCALE",
      defaultValue: "en",
    ),
    lightPrimary: String.fromEnvironment(
      "SP_LIGHT_PRIMARY",
      defaultValue: "40,170,170",
    ),
    darkPrimary: String.fromEnvironment(
      "SP_DARK_PRIMARY",
      defaultValue: "35,200,205",
    ),
    enableMockAuth: bool.fromEnvironment(
      "SP_ENABLE_MOCK_AUTH",
      defaultValue: true,
    ),
    enableOfflineCache: bool.fromEnvironment(
      "SP_ENABLE_OFFLINE_CACHE",
      defaultValue: true,
    ),
  );
}
