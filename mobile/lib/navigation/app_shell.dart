import 'package:flutter/material.dart';

import '../api/mobile_backend.dart';
import '../config/app_config.dart';
import '../features/auth/login_screen.dart';
import '../features/documents/documents_screen.dart';
import '../features/home/home_screen.dart';
import '../features/info_feed/info_feed_screen.dart';
import '../features/patrol/patrol_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/schedule/schedule_screen.dart';
import '../features/time_capture/time_capture_screen.dart';
import '../features/watchbook/watchbook_screen.dart';
import '../l10n/app_localizations.dart';
import '../session/mobile_session_controller.dart';
import 'app_destination.dart';

class AppShell extends StatefulWidget {
  const AppShell({
    required this.config,
    required this.backend,
    required this.controller,
    required this.themeMode,
    required this.locale,
    required this.onThemeModeChanged,
    required this.onLocaleChanged,
    super.key,
  });

  final AppConfig config;
  final MobileBackendGateway backend;
  final MobileSessionController controller;
  final ThemeMode themeMode;
  final Locale locale;
  final ValueChanged<ThemeMode> onThemeModeChanged;
  final ValueChanged<Locale> onLocaleChanged;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  AppDestination _destination = AppDestination.home;

  @override
  void initState() {
    super.initState();
    widget.controller.bootstrap();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        switch (widget.controller.phase) {
          case MobileSessionPhase.bootstrapping:
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          case MobileSessionPhase.unauthenticated:
            return LoginScreen(
              busy: widget.controller.busy,
              messageKey: widget.controller.messageKey,
              onLogin:
                  ({
                    required tenantCode,
                    required identifier,
                    required password,
                    required deviceLabel,
                    required deviceId,
                  }) {
                    return widget.controller.login(
                      tenantCode: tenantCode,
                      identifier: identifier,
                      password: password,
                      deviceLabel: deviceLabel,
                      deviceId: deviceId,
                    );
                  },
            );
          case MobileSessionPhase.forbidden:
          case MobileSessionPhase.blocked:
          case MobileSessionPhase.error:
            return Scaffold(
              body: Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    context.l10n.backendMessage(
                      widget.controller.messageKey ??
                          'errors.platform.internal',
                    ),
                  ),
                ),
              ),
            );
          case MobileSessionPhase.authenticated:
            return _buildAuthenticatedShell(context);
        }
      },
    );
  }

  Widget _buildAuthenticatedShell(BuildContext context) {
    final l10n = context.l10n;
    final destinations = _visibleDestinations();
    final screenWidth = MediaQuery.sizeOf(context).width;
    final compactNavigation = screenWidth < 430 && destinations.length > 4;
    if (!destinations.contains(_destination)) {
      _destination = destinations.first;
    }

    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 220),
        child: KeyedSubtree(
          key: ValueKey(_destination),
          child: switch (_destination) {
            AppDestination.home => HomeScreen(
              config: widget.config,
              controller: widget.controller,
              backend: widget.backend,
            ),
            AppDestination.schedule => ScheduleScreen(
              controller: widget.controller,
              backend: widget.backend,
            ),
            AppDestination.timeCapture => TimeCaptureScreen(
              controller: widget.controller,
              backend: widget.backend,
            ),
            AppDestination.updates => InfoFeedScreen(
              controller: widget.controller,
              backend: widget.backend,
            ),
            AppDestination.documents => DocumentsScreen(
              controller: widget.controller,
              backend: widget.backend,
            ),
            AppDestination.watchbook => WatchbookScreen(
              controller: widget.controller,
              backend: widget.backend,
            ),
            AppDestination.patrol => PatrolScreen(
              controller: widget.controller,
              backend: widget.backend,
            ),
            AppDestination.profile => ProfileScreen(
              config: widget.config,
              controller: widget.controller,
              backend: widget.backend,
              themeMode: widget.themeMode,
              locale: widget.locale,
              onThemeModeChanged: widget.onThemeModeChanged,
              onLocaleChanged: widget.onLocaleChanged,
            ),
          },
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: destinations.indexOf(_destination),
        labelBehavior: compactNavigation
            ? NavigationDestinationLabelBehavior.alwaysHide
            : NavigationDestinationLabelBehavior.alwaysShow,
        destinations: destinations
            .map(
              (destination) => NavigationDestination(
                icon: Icon(destination.icon),
                label: l10n.navLabel(destination.id),
              ),
            )
            .toList(growable: false),
        onDestinationSelected: (index) {
          setState(() {
            _destination = destinations[index];
          });
        },
      ),
    );
  }

  List<AppDestination> _visibleDestinations() {
    final mobileContext = widget.controller.context!;
    final items = <AppDestination>[
      AppDestination.home,
      if (mobileContext.hasScheduleAccess) AppDestination.schedule,
      if (mobileContext.hasTimeCaptureAccess) AppDestination.timeCapture,
      if (mobileContext.hasNoticeAccess) AppDestination.updates,
      if (mobileContext.hasDocumentAccess) AppDestination.documents,
      if (mobileContext.hasWatchbookAccess) AppDestination.watchbook,
      if (mobileContext.hasPatrolAccess) AppDestination.patrol,
      AppDestination.profile,
    ];
    return items;
  }
}
