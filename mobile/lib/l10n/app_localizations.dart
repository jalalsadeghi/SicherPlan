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
    'timeCapture' => isGerman ? 'Zeit' : 'Time',
    'updates' => isGerman ? 'Info' : 'Updates',
    'documents' => isGerman ? 'Dokumente' : 'Documents',
    'watchbook' => isGerman ? 'Wachbuch' : 'Watchbook',
    'patrol' => isGerman ? 'Patrouille' : 'Patrol',
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
  String homeHeroIdentity(String personnelNo, String fullName) =>
      '$personnelNo • $fullName';
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
  String get scheduleErrorTitle => isGerman
      ? 'Plan konnte nicht geladen werden'
      : 'Schedule could not be loaded';
  String get scheduleEmptyTitle =>
      isGerman ? 'Keine freigegebenen Schichten' : 'No released shifts';
  String get scheduleEmptySubtitle => isGerman
      ? 'Sobald eine Schicht freigegeben ist, erscheint sie hier in der Wochenansicht.'
      : 'Released shifts will appear here in the weekly view.';
  String scheduleWeekLabel(String start, String end) =>
      isGerman ? 'Woche $start - $end' : 'Week $start - $end';
  String get scheduleNoShift => isGerman ? 'Keine Schicht' : 'No shift';
  String get scheduleNoShifts => isGerman ? 'Keine Schichten' : 'No shifts';
  String get scheduleShiftDetailsTitle =>
      isGerman ? 'Schichtdetails' : 'Shift details';
  String get scheduleCloseAction => isGerman ? 'Schliessen' : 'Close';
  String get scheduleTodayLabel => isGerman ? 'Heute' : 'Today';
  String get scheduleDateLabel => isGerman ? 'Datum' : 'Date';
  String get scheduleTimeLabel => isGerman ? 'Zeit' : 'Time';
  String get scheduleLocationLabel => isGerman ? 'Ort' : 'Location';
  String get scheduleAssignmentStatusLabel =>
      isGerman ? 'Zuweisungsstatus' : 'Assignment status';
  String get scheduleConfirmationStatusLabel =>
      isGerman ? 'Bestaetigungsstatus' : 'Confirmation status';
  String get scheduleMeetingPoint => isGerman ? 'Treffpunkt' : 'Meeting point';
  String get scheduleMapAction => isGerman ? 'Route kopieren' : 'Copy route';
  String get scheduleConfirmAction => isGerman ? 'Bestaetigen' : 'Confirm';
  String get scheduleDeclineAction => isGerman ? 'Ablehnen' : 'Decline';
  String get scheduleCalendarExportAction =>
      isGerman ? 'Kalenderexport' : 'Calendar export';
  String get scheduleDocumentsTitle =>
      isGerman ? 'Freigegebene Unterlagen' : 'Released documents';
  String get scheduleDocumentsEmpty => isGerman
      ? 'Keine freigegebenen Unterlagen verknuepft.'
      : 'No released documents linked.';
  String get scheduleMapCopied => isGerman
      ? 'Die Karten-Route wurde in die Zwischenablage kopiert.'
      : 'The map route was copied to the clipboard.';
  String get scheduleConfirmDone =>
      isGerman ? 'Die Schicht wurde bestaetigt.' : 'The shift was confirmed.';
  String get scheduleDeclineDone =>
      isGerman ? 'Die Schicht wurde abgelehnt.' : 'The shift was declined.';
  String scheduleCalendarExported(String path) => isGerman
      ? 'Kalenderdatei gespeichert: $path'
      : 'Calendar file saved: $path';
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
  String get feedErrorTitle => isGerman
      ? 'Hinweise konnten nicht geladen werden'
      : 'Notices could not be loaded';
  String get feedEmptyTitle => isGerman ? 'Keine Hinweise' : 'No notices';
  String get feedEmptySubtitle => isGerman
      ? 'Es gibt aktuell keine veroeffentlichten Hinweise fuer dein Profil.'
      : 'There are currently no published notices for your profile.';
  String get noticeAcknowledgedBadge => isGerman ? 'Gelesen' : 'Read';
  String get noticeUnreadBadge => isGerman ? 'Neu' : 'New';
  String get noticeOpenAction => isGerman ? 'Oeffnen' : 'Open';
  String get noticeAcknowledgeAction =>
      isGerman ? 'Bestaetigen' : 'Acknowledge';
  String get noticeOpened =>
      isGerman ? 'Hinweis wurde geoeffnet.' : 'Notice opened.';
  String get noticeAcknowledgedDone =>
      isGerman ? 'Hinweis wurde bestaetigt.' : 'Notice acknowledged.';
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
  String get timeErrorTitle => isGerman
      ? 'Zeiterfassung konnte nicht geladen werden'
      : 'Time capture could not be loaded';
  String get timeEmptyTitle => isGerman
      ? 'Keine freigegebene Schicht fuer die Zeiterfassung'
      : 'No released shift for time capture';
  String get timeEmptySubtitle => isGerman
      ? 'Sobald eine freigegebene Schicht vorliegt, kann hier eingestempelt werden.'
      : 'As soon as a released shift exists, time capture will be available here.';
  String get timeCaptureFormTitle =>
      isGerman ? 'Zeitereignis erfassen' : 'Capture time event';
  String get timeCaptureFormSubtitle => isGerman
      ? 'Die App sendet ein mobiles Rohereignis an das echte Backend.'
      : 'The app sends a mobile raw event to the real backend.';
  String get timeShiftLabel => isGerman ? 'Schicht' : 'Shift';
  String get timeEventCodeLabel => isGerman ? 'Ereignis' : 'Event';
  String get timeScanMediumLabel => isGerman ? 'Scanmedium' : 'Scan medium';
  String get timeTokenLabel =>
      isGerman ? 'Token / Badgewert' : 'Token / badge value';
  String get timeTokenHint => isGerman
      ? 'Optional fuer QR, Barcode, RFID, NFC oder App-Badge'
      : 'Optional for QR, barcode, RFID, NFC, or app badge';
  String get timeLatitudeLabel => isGerman ? 'Breitengrad' : 'Latitude';
  String get timeLongitudeLabel => isGerman ? 'Laengengrad' : 'Longitude';
  String get timeNoteLabel => isGerman ? 'Notiz' : 'Note';
  String get timeSubmitAction => isGerman ? 'Jetzt buchen' : 'Submit now';
  String get timeSubmitSuccess => isGerman
      ? 'Zeiterfassung wurde uebermittelt.'
      : 'Time capture was submitted.';
  String get timeHistoryTitle =>
      isGerman ? 'Letzte Rohereignisse' : 'Recent raw events';
  String get timeHistoryEmptySubtitle => isGerman
      ? 'Noch keine Zeitereignisse fuer dein Profil.'
      : 'No time events for your profile yet.';

  String get patrolTitle => isGerman ? 'Patrouille' : 'Patrol';
  String get patrolSubtitle => isGerman
      ? 'Rundengaenge, Checkpoints und Offline-Synchronisation'
      : 'Rounds, checkpoints, and offline synchronization';
  String patrolAccessTitle(bool hasAccess) => hasAccess
      ? (isGerman ? 'Patrouille freigegeben' : 'Patrol enabled')
      : (isGerman ? 'Patrouille ausgeblendet' : 'Patrol hidden');
  String patrolAccessSubtitle(bool hasAccess) => hasAccess
      ? (isGerman
            ? 'Freigegebene Routen, Scanwege und Offline-Warteschlange bleiben auf den eigenen Mitarbeitendenkontext begrenzt.'
            : 'Released routes, scan flows, and the offline queue stay limited to the own employee context.')
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
  String get patrolErrorTitle => isGerman
      ? 'Patrouille konnte nicht geladen werden'
      : 'Patrol could not be loaded';
  String get patrolEmptyTitle =>
      isGerman ? 'Keine freigegebene Patrouille' : 'No released patrol route';
  String get patrolEmptySubtitle => isGerman
      ? 'Sobald eine freigegebene Route fuer deine Schicht vorliegt, erscheint sie hier.'
      : 'Released patrol routes for your shift will appear here.';
  String get patrolStartAction => isGerman ? 'Runde starten' : 'Start round';
  String get patrolCaptureTitle =>
      isGerman ? 'Checkpoint erfassen' : 'Capture checkpoint';
  String get patrolScanMethodLabel => isGerman ? 'Scanmethode' : 'Scan method';
  String get patrolTokenLabel =>
      isGerman ? 'Token / Scanwert' : 'Token / scan value';
  String get patrolNoteLabel => isGerman ? 'Notiz' : 'Note';
  String get patrolCheckpointCountLabel =>
      isGerman ? 'Checkpoints' : 'checkpoints';
  String get patrolCaptureAction => isGerman ? 'Erfassen' : 'Capture';
  String get patrolCompleteAction =>
      isGerman ? 'Runde beenden' : 'Complete round';
  String get patrolAbortAction => isGerman ? 'Abbrechen' : 'Abort round';
  String get patrolAbortReasonLabel =>
      isGerman ? 'Abbruchgrund' : 'Abort reason';
  String get patrolCheckpointDone => isGerman ? 'Erfasst' : 'Done';
  String get patrolInProgressTitle =>
      isGerman ? 'Aktive Patrouillenrunde' : 'Active patrol round';
  String get patrolEvaluationTitle => isGerman ? 'Auswertung' : 'Evaluation';
  String patrolEvaluationSummary(
    String statusCode,
    int exceptionCount,
    int manualCaptureCount,
  ) => isGerman
      ? 'Status: $statusCode | Ausnahmen: $exceptionCount | Manuell: $manualCaptureCount'
      : 'Status: $statusCode | Exceptions: $exceptionCount | Manual: $manualCaptureCount';
  String patrolQueuedBadge(int count) =>
      isGerman ? '$count in Warteschlange' : '$count queued';
  String patrolStatusLabel(String statusCode) => switch (statusCode) {
    'active' => isGerman ? 'Aktiv' : 'Active',
    'completed' => isGerman ? 'Abgeschlossen' : 'Completed',
    'aborted' => isGerman ? 'Abgebrochen' : 'Aborted',
    _ => statusCode,
  };

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

  String get mobileLoginTitle => isGerman ? 'Mitarbeiter-App' : 'Employee app';
  String get mobileLoginSubtitle => isGerman
      ? 'Anmeldung mit eigenem Mitarbeiter-Kontext'
      : 'Sign in with your employee context';
  String get mobileLoginTenantBanner =>
      isGerman ? 'Mandantenlogin' : 'Tenant login';
  String get mobileLoginFormTitle =>
      isGerman ? 'Sitzung starten' : 'Start session';
  String get mobileLoginFormSubtitle => isGerman
      ? 'Nur freigegebene und eigene Daten werden nach der Anmeldung geladen.'
      : 'Only released and own-record data is loaded after sign-in.';
  String get mobileLoginTenantLabel => isGerman ? 'Mandant' : 'Tenant';
  String get mobileLoginIdentifierLabel =>
      isGerman ? 'Benutzername oder E-Mail' : 'Username or email';
  String get mobileLoginPasswordLabel => isGerman ? 'Passwort' : 'Password';
  String get mobileLoginSubmit => isGerman ? 'Anmelden' : 'Sign in';
  String get mobileValidationRequired =>
      isGerman ? 'Pflichtfeld' : 'Required field';
  String get mobileIdentityTitle =>
      isGerman ? 'Eigener Mitarbeiterkontext' : 'Own employee context';
  String get mobileShellGuardsTitle =>
      isGerman ? 'Rollen- und Mandantenschutz' : 'Role and tenant guard';
  String get mobileShellGuardsSubtitle => isGerman
      ? 'Die Navigation bleibt auf den eigenen Mitarbeiterkontext und freigegebene Daten begrenzt.'
      : 'Navigation stays limited to the linked employee context and released data.';
  String mobileLoadErrorSubtitle(Object? error) => isGerman
      ? 'Der Ladevorgang ist fehlgeschlagen: ${error ?? 'Unbekannt'}'
      : 'Loading failed: ${error ?? 'Unknown'}';
  String get mobileStatusConfirmed => isGerman ? 'Bestaetigt' : 'Confirmed';
  String get mobileStatusAssigned => isGerman ? 'Zugewiesen' : 'Assigned';
  String get mobileStatusDeclined => isGerman ? 'Abgelehnt' : 'Declined';
  String get mobileLogoutAction => isGerman ? 'Abmelden' : 'Log out';

  String get eventApplicationTitle =>
      isGerman ? 'Veranstaltungsbewerbung' : 'Event application';
  String get eventApplicationSubtitle => isGerman
      ? 'Freie Veranstaltungswuensche laufen ueber die freigegebene HR/Planungs-Schnittstelle.'
      : 'Event applications use the approved HR/planning seam.';
  String get eventApplicationPlanningRecordLabel =>
      isGerman ? 'Planungsdatensatz-ID' : 'Planning record ID';
  String get eventApplicationNoteLabel => isGerman ? 'Notiz' : 'Note';
  String get eventApplicationSubmit => isGerman ? 'Bewerben' : 'Apply';
  String get eventApplicationEmpty =>
      isGerman ? 'Noch keine Bewerbungen vorhanden.' : 'No applications yet.';
  String get eventApplicationCancel => isGerman ? 'Zurueckziehen' : 'Withdraw';
  String get eventApplicationCreated => isGerman
      ? 'Die Bewerbung wurde angelegt.'
      : 'The application was created.';
  String get eventApplicationCancelled => isGerman
      ? 'Die Bewerbung wurde zurueckgezogen.'
      : 'The application was withdrawn.';

  String get documentsTitle => isGerman ? 'Dokumente' : 'Documents';
  String get documentsSubtitle => isGerman
      ? 'Eigene Unterlagen und freigegebene Schichtdokumente'
      : 'Own documents and released shift files';
  String get documentsErrorTitle => isGerman
      ? 'Dokumente konnten nicht geladen werden'
      : 'Documents could not be loaded';
  String get documentsEmptyTitle =>
      isGerman ? 'Keine freigegebenen Dokumente' : 'No released documents';
  String get documentsEmptySubtitle => isGerman
      ? 'Sobald Dokumente fuer dich freigegeben oder verknuepft sind, erscheinen sie hier.'
      : 'Released or linked documents will appear here.';
  String get documentsDownloadUnavailable => isGerman
      ? 'Dieses Dokument ist noch nicht downloadbar.'
      : 'This document is not downloadable yet.';
  String documentsDownloaded(String path) =>
      isGerman ? 'Dokument gespeichert: $path' : 'Document saved: $path';

  String get watchbookTitle => isGerman ? 'Wachbuch' : 'Watchbook';
  String get watchbookSubtitle => isGerman
      ? 'Freigegebene Wachbucheintraege und Aufsichtshinweise im Mitarbeiterkontext'
      : 'Released watchbook entries and supervision notes in the employee context';
  String get watchbookPlaceholderTitle =>
      isGerman ? 'Noch keine Wachbuecher' : 'No watchbooks yet';
  String get watchbookPlaceholderSubtitle => isGerman
      ? 'Sobald fuer deine freigegebenen Schichten Wachbuecher vorliegen, erscheinen sie hier.'
      : 'Watchbooks will appear here as soon as they exist for your released shifts.';
  String get watchbookEntryLabel => isGerman ? 'Neuer Eintrag' : 'New entry';
  String get watchbookEntryAction =>
      isGerman ? 'Eintrag speichern' : 'Save entry';
  String get watchbookEntrySaved => isGerman
      ? 'Wachbucheintrag wurde gespeichert.'
      : 'Watchbook entry saved.';

  String get credentialsTitle =>
      isGerman ? 'Ausweise und Codes' : 'Credentials and codes';
  String get credentialsErrorTitle => isGerman
      ? 'Ausweise konnten nicht geladen werden'
      : 'Credentials could not be loaded';
  String get credentialsEmptyTitle =>
      isGerman ? 'Keine aktiven Ausweise' : 'No active credentials';
  String get credentialsEmptySubtitle => isGerman
      ? 'Sobald ein Ausweis freigegeben ist, erscheint er hier fuer QR-/Barcode-Nutzung.'
      : 'Released credentials will appear here for QR/barcode use.';

  String backendMessage(String messageKey) => switch (messageKey) {
    'errors.platform.internal' =>
      isGerman
          ? 'Es ist ein interner Plattformfehler aufgetreten.'
          : 'An internal platform error has occurred.',
    'errors.iam.auth.invalid_credentials' =>
      isGerman
          ? 'Die Anmeldedaten sind ungueltig.'
          : 'The login credentials are invalid.',
    'errors.iam.auth.invalid_access_token' =>
      isGerman
          ? 'Die Sitzung ist nicht mehr gueltig.'
          : 'The session is no longer valid.',
    'errors.iam.authorization.permission_denied' =>
      isGerman
          ? 'Der Zugriff auf die Mitarbeiter-App wurde verweigert.'
          : 'Access to the employee app was denied.',
    'errors.employees.self_service.employee_not_found' =>
      isGerman
          ? 'Es wurde kein aktiver Mitarbeiterkontext gefunden.'
          : 'No active employee context was found.',
    'errors.employees.self_service.employee_inactive' =>
      isGerman
          ? 'Die Mitarbeitenden-Verknuepfung ist inaktiv.'
          : 'The employee linkage is inactive.',
    'errors.planning.assignment.response_invalid' =>
      isGerman
          ? 'Die Schichtrueckmeldung ist ungueltig.'
          : 'The shift response is invalid.',
    'errors.field.patrol_round.active_exists' =>
      isGerman
          ? 'Es existiert bereits eine aktive Patrouillenrunde.'
          : 'There is already an active patrol round.',
    'errors.field.patrol_round.shift_not_assigned' =>
      isGerman
          ? 'Diese Patrouille ist nicht fuer dich freigegeben.'
          : 'This patrol is not released to you.',
    'errors.field.patrol_round.route_not_found' =>
      isGerman
          ? 'Die Patrouillenroute wurde nicht gefunden.'
          : 'The patrol route was not found.',
    'errors.field.patrol_round.not_active' =>
      isGerman
          ? 'Die Patrouillenrunde ist nicht mehr aktiv.'
          : 'The patrol round is no longer active.',
    'errors.field.patrol_round.manual_reason_required' =>
      isGerman
          ? 'Manuelle Erfassung benoetigt Grund oder Notiz.'
          : 'Manual capture requires a reason or note.',
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
