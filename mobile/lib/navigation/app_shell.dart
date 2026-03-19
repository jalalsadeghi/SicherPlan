import 'package:flutter/material.dart';

import '../config/app_config.dart';
import '../l10n/app_localizations.dart';
import '../features/home/home_screen.dart';
import '../features/info_feed/info_feed_screen.dart';
import '../features/patrol/patrol_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/schedule/schedule_screen.dart';
import '../features/time_capture/time_capture_screen.dart';
import '../session/mobile_role.dart';
import '../session/mobile_session.dart';
import 'app_destination.dart';

class AppShell extends StatefulWidget {
  const AppShell({
    required this.config,
    required this.themeMode,
    required this.locale,
    required this.onThemeModeChanged,
    required this.onLocaleChanged,
    super.key,
  });

  final AppConfig config;
  final ThemeMode themeMode;
  final Locale locale;
  final ValueChanged<ThemeMode> onThemeModeChanged;
  final ValueChanged<Locale> onLocaleChanged;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  late MobileSession _session;
  AppDestination _destination = AppDestination.home;

  @override
  void initState() {
    super.initState();
    _session = MobileSession.initial(widget.config);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final destinations = _visibleDestinations(_session);

    if (!destinations.contains(_destination)) {
      _destination = destinations.first;
    }

    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 220),
        child: KeyedSubtree(
          key: ValueKey(_destination),
          child: _buildScreen(_destination),
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: destinations.indexOf(_destination),
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

  Widget _buildScreen(AppDestination destination) {
    switch (destination) {
      case AppDestination.home:
        return HomeScreen(
          config: widget.config,
          session: _session,
          onRoleChanged: _handleRoleChanged,
        );
      case AppDestination.schedule:
        return ScheduleScreen(role: _session.role);
      case AppDestination.updates:
        return const InfoFeedScreen();
      case AppDestination.timeCapture:
        return TimeCaptureScreen(
          role: _session.role,
          offlineReady: _session.offlineReady,
        );
      case AppDestination.patrol:
        return PatrolScreen(session: _session);
      case AppDestination.profile:
        return ProfileScreen(
          config: widget.config,
          session: _session,
          themeMode: widget.themeMode,
          locale: widget.locale,
          onThemeModeChanged: widget.onThemeModeChanged,
          onLocaleChanged: widget.onLocaleChanged,
        );
    }
  }

  List<AppDestination> _visibleDestinations(MobileSession session) {
    final destinations = <AppDestination>[
      AppDestination.home,
      AppDestination.schedule,
      AppDestination.updates,
      AppDestination.timeCapture,
      AppDestination.profile,
    ];

    if (session.hasPatrolAccess || session.role == MobileRole.fieldSupervisor) {
      destinations.insert(4, AppDestination.patrol);
    }

    return destinations;
  }

  void _handleRoleChanged(MobileRole? role) {
    if (role == null) {
      return;
    }

    setState(() {
      _session = _session.copyWith(
        role: role,
        hasPatrolAccess: role != MobileRole.restrictedField,
      );
    });
  }
}
