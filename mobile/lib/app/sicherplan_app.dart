import 'package:flutter/material.dart';

import '../api/mobile_backend.dart';
import '../config/app_config.dart';
import '../l10n/app_localizations.dart';
import '../navigation/app_shell.dart';
import '../session/mobile_session_controller.dart';
import '../session/mobile_session_store.dart';
import 'sicherplan_theme.dart';

class SicherPlanApp extends StatefulWidget {
  const SicherPlanApp({
    required this.config,
    this.backendOverride,
    this.storeOverride,
    super.key,
  });

  final AppConfig config;
  final MobileBackendGateway? backendOverride;
  final MobileSessionStore? storeOverride;

  @override
  State<SicherPlanApp> createState() => _SicherPlanAppState();
}

class _SicherPlanAppState extends State<SicherPlanApp> {
  ThemeMode _themeMode = ThemeMode.light;
  late Locale _locale;
  late final MobileSessionController _controller;
  late final MobileBackendGateway _backend;

  @override
  void initState() {
    super.initState();
    _locale = Locale(widget.config.defaultLocale);
    _backend = widget.backendOverride ?? HttpMobileBackendGateway(config: widget.config);
    _controller = MobileSessionController(
      backend: _backend,
      store: widget.storeOverride ?? FileMobileSessionStore(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      onGenerateTitle: (context) => context.l10n.appTitle,
      debugShowCheckedModeBanner: false,
      locale: _locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      themeMode: _themeMode,
      theme: resolveSicherPlanTheme(
        mode: ThemeMode.light,
        lightPrimaryConfig: widget.config.lightPrimary,
        darkPrimaryConfig: widget.config.darkPrimary,
      ),
      darkTheme: resolveSicherPlanTheme(
        mode: ThemeMode.dark,
        lightPrimaryConfig: widget.config.lightPrimary,
        darkPrimaryConfig: widget.config.darkPrimary,
      ),
      home: AppShell(
        config: widget.config,
        backend: _backend,
        controller: _controller,
        themeMode: _themeMode,
        locale: _locale,
        onThemeModeChanged: (mode) {
          setState(() {
            _themeMode = mode;
          });
        },
        onLocaleChanged: (locale) {
          setState(() {
            _locale = locale;
          });
        },
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
