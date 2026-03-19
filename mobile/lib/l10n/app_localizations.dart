import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import '../session/mobile_role.dart';

class AppLocalizations {
  const AppLocalizations(this.locale);

  final Locale locale;

  static const supportedLocales = [Locale('de'), Locale('en')];

  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates = [
    _AppLocalizationsDelegate(),
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ];

  static AppLocalizations of(BuildContext context) {
    final localization = Localizations.of<AppLocalizations>(
      context,
      AppLocalizations,
    );
    assert(localization != null, 'AppLocalizations not found in context');
    return localization!;
  }

  bool get isGerman => locale.languageCode == 'de';

  String get appTitle => 'SicherPlan';

  String get localeLabel => isGerman ? 'Sprache' : 'Language';
  String get localeGerman => isGerman ? 'Deutsch' : 'German';
  String get localeEnglish => isGerman ? 'Englisch' : 'English';

  String navLabel(String destination) => switch (destination) {
    'home' => isGerman ? 'Start' : 'Home',
    'schedule' => isGerman ? 'Plan' : 'Schedule',
    'updates' => isGerman ? 'Info' : 'Updates',
    'timeCapture' => isGerman ? 'Zeit' : 'Time',
    'patrol' => 'Watchbook',
    'profile' => isGerman ? 'Profil' : 'Profile',
    _ => destination,
  };

  String roleLabel(MobileRole role) => switch (role) {
    MobileRole.employee => isGerman ? 'Mitarbeiter' : 'Employee',
    MobileRole.fieldSupervisor =>
      isGerman ? 'Einsatzleitung' : 'Field supervisor',
    MobileRole.restrictedField =>
      isGerman ? 'Feldeinsatz eingeschraenkt' : 'Restricted field',
  };

  String roleDescription(MobileRole role) => switch (role) {
    MobileRole.employee =>
      isGerman
          ? 'Standardzugriff auf freigegebene Einsatz- und Selbstservice-Daten.'
          : 'Standard access to released assignment and self-service data.',
    MobileRole.fieldSupervisor =>
      isGerman
          ? 'Zusatzsicht auf Teamkoordination, Watchbook und operative Hinweise.'
          : 'Additional view for team coordination, watchbook, and operational notices.',
    MobileRole.restrictedField =>
      isGerman
          ? 'Reduzierte Sicht auf zugewiesene Aufgaben fuer sensible oder externe Einsaetze.'
          : 'Reduced view of assigned tasks for sensitive or external deployments.',
  };

  String get homeTitle => isGerman ? 'SicherPlan Mobil' : 'SicherPlan Mobile';
  String get homeSubtitle => isGerman
      ? 'Freigegebene Einsaetze, Meldungen und Selbstservice'
      : 'Released assignments, notices, and self-service';
  String homeGreeting(String userName) =>
      isGerman ? 'Hallo $userName' : 'Hello $userName';
  String get homeBannerSubtitle => isGerman
      ? 'Bereit fuer mobile Feld- und Mitarbeiterprozesse.'
      : 'Ready for mobile field and employee workflows.';
  String get todayReleasedTitle =>
      isGerman ? 'Heute freigegeben' : 'Released today';
  String get todayReleasedSubtitle => isGerman
      ? '2 Schichten, 1 Pflichtmeldung, 1 Watchbook-Hinweis'
      : '2 shifts, 1 required notice, 1 watchbook hint';
  String get offlineReadinessTitle =>
      isGerman ? 'Offline-Bereitschaft' : 'Offline readiness';
  String offlineReadinessSubtitle(bool enabled) => enabled
      ? (isGerman
            ? 'Der Shell-Aufbau bleibt fuer spaetere Offline-Sync-Flows vorbereitet.'
            : 'The shell remains ready for later offline sync flows.')
      : (isGerman
            ? 'Offline-Sync ist in dieser Umgebung deaktiviert.'
            : 'Offline sync is disabled in this environment.');

  String get roleViewTitle => isGerman ? 'Rollenansicht' : 'Role view';
  String get roleViewSubtitle => isGerman
      ? 'Mock-Umschaltung fuer Navigation und Sichtrechte in der Shell.'
      : 'Mock switch for navigation and visibility rules in the shell.';
  String get activeMobileRoleLabel =>
      isGerman ? 'Aktive mobile Rolle' : 'Active mobile role';

  String get scheduleTitle => isGerman ? 'Einsatzplan' : 'Schedule';
  String get scheduleSubtitle => isGerman
      ? 'Nur freigegebene Schichten und operative Details'
      : 'Only released shifts and operational details';
  String get scheduleCardTitle =>
      isGerman ? 'Mo, 22.03. 06:00-14:00' : 'Mon, 22 Mar 06:00-14:00';
  String get scheduleCardSubtitle => isGerman
      ? 'Objektschutz Hafen Nord | Treffpunkt Tor B'
      : 'Site security Hafen Nord | Meeting point Gate B';
  String get releasedBadge => isGerman ? 'Freigegeben' : 'Released';
  String schedulePrepTitle(MobileRole role) =>
      role == MobileRole.fieldSupervisor
      ? (isGerman ? 'Teamuebergabe' : 'Team handover')
      : (isGerman ? 'Dienstbeginn vorbereiten' : 'Prepare shift start');
  String schedulePrepSubtitle(MobileRole role) =>
      role == MobileRole.fieldSupervisor
      ? (isGerman
            ? 'Supervisor-Sicht zeigt Teamstatus und Sammelhinweise.'
            : 'Supervisor view shows team status and consolidated notices.')
      : (isGerman
            ? 'Standard-Sicht bleibt auf eigene Zuweisungen begrenzt.'
            : 'Standard view remains limited to own assignments.');

  String get feedTitle => isGerman ? 'Infoboard' : 'Info board';
  String get feedSubtitle => isGerman
      ? 'Einsatzhinweise, Sicherheitsmeldungen und Teamupdates'
      : 'Assignment notices, security alerts, and team updates';
  String get feedTrafficTitle =>
      isGerman ? 'Lagehinweis' : 'Operational notice';
  String get feedTrafficSubtitle => isGerman
      ? 'Anfahrt Westtor ab 18:00 wegen Veranstaltung gesperrt.'
      : 'Access via west gate closed from 18:00 due to event.';
  String get newBadge => isGerman ? 'Neu' : 'New';
  String get feedUniformTitle => isGerman ? 'Dienstanweisung' : 'Instruction';
  String get feedUniformSubtitle => isGerman
      ? 'Uniformkontrolle vor Schichtstart digital bestaetigen.'
      : 'Confirm uniform check digitally before shift start.';

  String get timeTitle => isGerman ? 'Zeiterfassung' : 'Time capture';
  String get timeSubtitle => isGerman
      ? 'Rohereignisse bleiben korrekturfaehig und auditierbar'
      : 'Raw events stay correction-safe and auditable';
  String get timeStartTitle =>
      isGerman ? 'Dienstbeginn buchen' : 'Book shift start';
  String timeStartSubtitle(bool offlineReady) => offlineReady
      ? (isGerman
            ? 'Start/Stop-Flows koennen spaeter mit Offline-Sync erweitert werden.'
            : 'Start/stop flows can later be extended with offline sync.')
      : (isGerman
            ? 'In dieser Umgebung ist nur der Online-Pfad vorgesehen.'
            : 'Only the online path is enabled in this environment.');
  String timeModeBadge(bool offlineReady) =>
      offlineReady ? 'Offline-ready' : (isGerman ? 'Online' : 'Online');
  String timeApprovalTitle(MobileRole role) =>
      role == MobileRole.restrictedField
      ? (isGerman ? 'Eingeschraenkte Sicht' : 'Restricted view')
      : (isGerman
            ? 'Freigabe- und Korrekturpfad'
            : 'Approval and correction path');
  String timeApprovalSubtitle(MobileRole role) =>
      role == MobileRole.restrictedField
      ? (isGerman
            ? 'Eingeschraenkte Rolle sieht nur eigene Zeiterfassung.'
            : 'Restricted role only sees own time capture.')
      : (isGerman
            ? 'Spaetere Schritte koennen Supervisor- oder Backoffice-Freigaben anbinden.'
            : 'Later steps can attach supervisor or back-office approvals.');

  String get patrolTitle => 'Watchbook & Patrol';
  String get patrolSubtitle => isGerman
      ? 'Patrouillen, Rundengange und Vorfallhinweise'
      : 'Patrols, rounds, and incident notices';
  String patrolAccessTitle(bool hasAccess) => hasAccess
      ? (isGerman ? 'Watchbook freigegeben' : 'Watchbook released')
      : (isGerman ? 'Watchbook ausgeblendet' : 'Watchbook hidden');
  String patrolAccessSubtitle(bool hasAccess) => hasAccess
      ? (isGerman
            ? 'Die Shell reserviert Platz fuer spaetere Patrol-, NFC- und Scan-Flows.'
            : 'The shell reserves space for later patrol, NFC, and scan flows.')
      : (isGerman
            ? 'Patrol-Zugriff kann spaeter rollenbasiert wieder aktiviert werden.'
            : 'Patrol access can later be re-enabled by role.');
  String patrolAccessBadge(bool hasAccess) => hasAccess
      ? (isGerman ? 'Aktiv' : 'Active')
      : (isGerman ? 'Gesperrt' : 'Locked');
  String get patrolIncidentTitle =>
      isGerman ? 'Vorfallbericht' : 'Incident report';
  String get patrolIncidentSubtitle => isGerman
      ? 'Dokumente und Reports werden spaeter ueber den zentralen Docs-Service verknuepft.'
      : 'Documents and reports will later be linked through the central docs service.';

  String get profileTitle =>
      isGerman ? 'Profil & Einstellungen' : 'Profile and settings';
  String get profileSubtitle => isGerman
      ? 'Session, Sprache und Geraetevorgaben'
      : 'Session, language, and device settings';
  String profileRoleSubtitle(String tenantName, String roleLabel) => isGerman
      ? 'Mandant: $tenantName | Rolle: $roleLabel'
      : 'Tenant: $tenantName | Role: $roleLabel';
  String get languageBaselineTitle =>
      isGerman ? 'Sprachbaseline' : 'Language baseline';
  String languageBaselineSubtitle(
    String defaultLocale,
    String fallbackLocale,
  ) => isGerman
      ? 'DE ist Standard ($defaultLocale), EN bleibt sekundar ($fallbackLocale) fuer den naechsten i18n-Schritt.'
      : 'DE is the default ($defaultLocale), EN remains secondary ($fallbackLocale) for the next i18n step.';
  String get environmentTitle => isGerman ? 'Umgebung' : 'Environment';
  String apiSubtitle(String apiBaseUrl) => 'API $apiBaseUrl';

  String get themeCardTitle => isGerman ? 'Designmodus' : 'Theme mode';
  String get themeCardSubtitle => isGerman
      ? 'Sprint-1-Toggle fuer die zentralen Light/Dark-Token.'
      : 'Sprint 1 toggle for the centralized light/dark tokens.';
  String themeActiveTitle(bool isDark) => isDark
      ? (isGerman ? 'Dunkelmodus aktiv' : 'Dark mode active')
      : (isGerman ? 'Hellmodus aktiv' : 'Light mode active');
  String get themeActiveSubtitle => isGerman
      ? 'Primarfarben bleiben exakt auf den vorgegebenen SicherPlan-Werten.'
      : 'Primary colors stay exact to the required SicherPlan values.';

  String get localeCardTitle => isGerman ? 'Sprache' : 'Language';
  String get localeCardSubtitle => isGerman
      ? 'Deutsch ist Standard, Englisch bleibt die zweite Shell-Sprache.'
      : 'German is the default and English remains the second shell language.';

  String backendMessage(String messageKey) => switch (messageKey) {
    'errors.platform.internal' =>
      isGerman
          ? 'Es ist ein interner Plattformfehler aufgetreten.'
          : 'An internal platform error has occurred.',
    _ => messageKey,
  };
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => AppLocalizations.supportedLocales.any(
    (supported) => supported.languageCode == locale.languageCode,
  );

  @override
  Future<AppLocalizations> load(Locale locale) async {
    return AppLocalizations(locale);
  }

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

extension AppLocalizationsX on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);
}
