import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sicherplan_mobile/api/mobile_backend.dart';
import 'package:sicherplan_mobile/features/schedule/schedule_screen.dart';
import 'package:sicherplan_mobile/l10n/app_localizations.dart';
import 'package:sicherplan_mobile/session/mobile_session_controller.dart';
import 'package:sicherplan_mobile/session/mobile_session_store.dart';

class _MemoryStore implements MobileSessionStore {
  StoredMobileSession? value;

  @override
  Future<void> clear() async {
    value = null;
  }

  @override
  Future<StoredMobileSession?> read() async => value;

  @override
  Future<void> write(StoredMobileSession session) async {
    value = session;
  }
}

class _ScheduleBackend implements MobileBackendGateway {
  _ScheduleBackend({required this.schedules});

  final List<EmployeeReleasedScheduleItem> schedules;

  final user = const MobileCurrentUser(
    id: 'user-1',
    tenantId: 'tenant-1',
    username: 'anna',
    fullName: 'Anna Meyer',
    locale: 'de',
    timezone: 'Europe/Berlin',
    roleKeys: ['employee_user'],
    permissionKeys: ['portal.employee.access', 'platform.info.read'],
  );

  final tokens = const MobileAuthTokens(
    accessToken: 'access',
    refreshToken: 'refresh',
    sessionId: 'session',
  );

  final context = const EmployeeMobileContext(
    tenantId: 'tenant-1',
    tenantCode: 'nord',
    tenantName: 'SicherPlan Nord',
    photoDocumentId: null,
    photoCurrentVersionNo: null,
    photoContentType: null,
    userId: 'user-1',
    employeeId: 'employee-1',
    personnelNo: 'EMP-1',
    fullName: 'Anna Meyer',
    preferredName: 'Anna',
    workEmail: 'anna@example.com',
    mobilePhone: '+49170',
    defaultBranchId: 'branch-1',
    defaultMandateId: 'mandate-1',
    locale: 'de',
    timezone: 'Europe/Berlin',
    appRole: 'employee',
    roleKeys: ['employee_user'],
    hasScheduleAccess: true,
    hasDocumentAccess: true,
    hasNoticeAccess: true,
    hasTimeCaptureAccess: true,
    hasWatchbookAccess: true,
    hasPatrolAccess: false,
  );

  @override
  Future<void> acknowledgeNotice(
    String accessToken,
    String tenantId,
    String noticeId, {
    String? acknowledgementText,
  }) async {}

  @override
  Future<EmployeeEventApplicationItem> cancelEventApplication(
    String accessToken, {
    required String applicationId,
    required int? versionNo,
    String? decisionNote,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<EmployeeEventApplicationItem> createEventApplication(
    String accessToken, {
    required String planningRecordId,
    String? note,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<List<int>> downloadNoticeAttachment(
    String accessToken, {
    required String tenantId,
    required String documentId,
    required int versionNo,
  }) async => <int>[];

  @override
  Future<List<int>> downloadOwnDocument(
    String accessToken, {
    required String documentId,
    required int versionNo,
  }) async => <int>[];

  @override
  Future<List<EmployeeMobileCredential>> fetchCredentials(
    String accessToken,
  ) async => const [];

  @override
  Future<List<EmployeeMobileDocument>> fetchDocuments(
    String accessToken,
  ) async => const [];

  @override
  Future<List<EmployeeEventApplicationItem>> fetchEventApplications(
    String accessToken,
  ) async => const [];

  @override
  Future<NoticeItem> fetchNotice(
    String accessToken,
    String tenantId,
    String noticeId,
  ) async {
    throw UnimplementedError();
  }

  @override
  Future<NoticeFeedStatus> fetchNoticeFeedStatus(
    String accessToken,
    String tenantId,
  ) async {
    throw UnimplementedError();
  }

  @override
  Future<List<NoticeItem>> fetchNotices(
    String accessToken,
    String tenantId,
  ) async => const [];

  @override
  Future<PatrolRoundItem?> fetchActivePatrolRound(String accessToken) async =>
      null;

  @override
  Future<EmployeeMobileContext> fetchMobileContext(String accessToken) async =>
      context;

  @override
  Future<PatrolEvaluationItem> fetchPatrolEvaluation(
    String accessToken,
    String patrolRoundId,
  ) async {
    throw UnimplementedError();
  }

  @override
  Future<List<PatrolAvailableRouteItem>> fetchPatrolRoutes(
    String accessToken,
  ) async => const [];

  @override
  Future<PatrolRoundItem> fetchPatrolRound(
    String accessToken,
    String patrolRoundId,
  ) async {
    throw UnimplementedError();
  }

  @override
  Future<List<EmployeeReleasedScheduleItem>> fetchReleasedSchedules(
    String accessToken,
  ) async => schedules;

  @override
  Future<List<TimeCaptureEventItem>> fetchTimeEvents(
    String accessToken,
  ) async => const [];

  @override
  Future<WatchbookReadModel> fetchWatchbook(
    String accessToken, {
    required String tenantId,
    required String watchbookId,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<List<WatchbookListItem>> fetchWatchbooks(
    String accessToken,
    String tenantId,
  ) async => const [];

  @override
  Future<(MobileCurrentUser, MobileAuthTokens)> login(
    MobileLoginPayload payload,
  ) async => (user, tokens);

  @override
  Future<void> openNotice(
    String accessToken,
    String tenantId,
    String noticeId,
  ) async {}

  @override
  Future<WatchbookReadModel> openWatchbook(
    String accessToken, {
    required String tenantId,
    required String contextType,
    required DateTime logDate,
    String? siteId,
    String? orderId,
    String? planningRecordId,
    String? shiftId,
    String? headline,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<EmployeeReleasedScheduleItem> respondToAssignment(
    String accessToken, {
    required String assignmentId,
    required String responseCode,
    required int? versionNo,
    String? note,
  }) async {
    return schedules.firstWhere((item) => item.id == assignmentId);
  }

  @override
  Future<(MobileCurrentUser, MobileAuthTokens)> restore(
    MobileAuthTokens tokens,
  ) async => (user, this.tokens);

  @override
  Future<PatrolRoundItem> abortPatrolRound(
    String accessToken,
    String patrolRoundId,
    PatrolRoundAbortPayload payload,
  ) async {
    throw UnimplementedError();
  }

  @override
  Future<PatrolRoundItem> capturePatrolCheckpoint(
    String accessToken,
    String patrolRoundId,
    PatrolRoundCapturePayload payload,
  ) async {
    throw UnimplementedError();
  }

  @override
  Future<PatrolRoundItem> completePatrolRound(
    String accessToken,
    String patrolRoundId,
    PatrolRoundCompletePayload payload,
  ) async {
    throw UnimplementedError();
  }

  @override
  Future<TimeCaptureEventItem> captureOwnTimeEvent(
    String accessToken, {
    required String sourceChannelCode,
    required TimeCapturePayload payload,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<WatchbookEntryItem> createWatchbookEntry(
    String accessToken, {
    required String tenantId,
    required String watchbookId,
    required String entryTypeCode,
    required String narrative,
    String? trafficLightCode,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<PatrolRoundItem> startPatrolRound(
    String accessToken,
    PatrolRoundStartPayload payload,
  ) async {
    throw UnimplementedError();
  }
}

Future<MobileSessionController> _buildAuthenticatedController(
  MobileBackendGateway backend,
) async {
  final controller = MobileSessionController(
    backend: backend,
    store: _MemoryStore(),
  );
  await controller.login(
    tenantCode: 'nord',
    identifier: 'anna',
    password: 'secret',
    deviceLabel: 'flutter',
    deviceId: 'device-1',
  );
  return controller;
}

Widget _buildHarness({
  required MobileSessionController controller,
  required MobileBackendGateway backend,
}) {
  return MaterialApp(
    locale: const Locale('de'),
    supportedLocales: AppLocalizations.supportedLocales,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    home: ScheduleScreen(controller: controller, backend: backend),
  );
}

EmployeeReleasedScheduleItem _schedule({
  required String id,
  required DateTime scheduleDate,
  required DateTime workStart,
  required DateTime workEnd,
  String shiftLabel = 'Tagdienst',
}) {
  return EmployeeReleasedScheduleItem(
    id: id,
    employeeId: 'employee-1',
    shiftId: 'shift-$id',
    planningRecordId: 'planning-$id',
    orderId: 'order-$id',
    siteId: 'site-$id',
    scheduleDate: scheduleDate,
    shiftLabel: shiftLabel,
    workStart: workStart,
    workEnd: workEnd,
    locationLabel: 'Objekt Nord',
    meetingPoint: 'Tor A',
    assignmentStatus: 'assigned',
    confirmationStatus: 'assigned',
    documents: const [
      EmployeeReleasedDocument(
        documentId: 'doc-1',
        title: 'Dienstanweisung',
        fileName: 'dienstanweisung.pdf',
        contentType: 'application/pdf',
        currentVersionNo: 1,
        relationType: 'deployment_output',
      ),
    ],
  );
}

void main() {
  testWidgets('schedule shows empty state when no released shifts exist', (
    tester,
  ) async {
    final backend = _ScheduleBackend(schedules: const []);
    final controller = await _buildAuthenticatedController(backend);

    await tester.pumpWidget(
      _buildHarness(controller: controller, backend: backend),
    );
    await tester.pumpAndSettle();

    expect(find.text('Keine freigegebenen Schichten'), findsOneWidget);
    expect(find.byKey(const ValueKey('schedule-calendar-grid')), findsNothing);
  });

  testWidgets(
    'schedule renders a calendar month view with highlighted shift days',
    (tester) async {
      final backend = _ScheduleBackend(
        schedules: [
          _schedule(
            id: 'a',
            scheduleDate: DateTime(2026, 4, 2),
            workStart: DateTime(2026, 4, 2, 8),
            workEnd: DateTime(2026, 4, 2, 16),
          ),
          _schedule(
            id: 'b',
            scheduleDate: DateTime(2026, 4, 2),
            workStart: DateTime(2026, 4, 2, 18),
            workEnd: DateTime(2026, 4, 2, 22),
            shiftLabel: 'Abenddienst',
          ),
          _schedule(
            id: 'c',
            scheduleDate: DateTime(2026, 4, 12),
            workStart: DateTime(2026, 4, 12, 6),
            workEnd: DateTime(2026, 4, 12, 14),
          ),
        ],
      );
      final controller = await _buildAuthenticatedController(backend);

      await tester.pumpWidget(
        _buildHarness(controller: controller, backend: backend),
      );
      await tester.pumpAndSettle();

      expect(
        find.byKey(const ValueKey('schedule-calendar-grid')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('schedule-calendar-month-label')),
        findsOneWidget,
      );
      expect(find.text('M'), findsWidgets);
      expect(
        find.byKey(const ValueKey('schedule-calendar-day-count-2026-04-02')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('event-application-planning-record-field')),
        findsNothing,
      );
    },
  );

  testWidgets(
    'schedule keeps event application collapsed so the calendar stays primary',
    (tester) async {
      final backend = _ScheduleBackend(
        schedules: [
          _schedule(
            id: 'a',
            scheduleDate: DateTime(2026, 4, 2),
            workStart: DateTime(2026, 4, 2, 8),
            workEnd: DateTime(2026, 4, 2, 16),
          ),
        ],
      );
      final controller = await _buildAuthenticatedController(backend);

      await tester.pumpWidget(
        _buildHarness(controller: controller, backend: backend),
      );
      await tester.pumpAndSettle();

      expect(
        find.byKey(const ValueKey('schedule-calendar-grid')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('event-application-planning-record-field')),
        findsNothing,
      );

      await tester.scrollUntilVisible(
        find.text('Veranstaltungsbewerbung'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();

      expect(find.text('Veranstaltungsbewerbung'), findsOneWidget);

      await tester.tap(find.text('Veranstaltungsbewerbung'));
      await tester.pumpAndSettle();

      expect(
        find.byKey(const ValueKey('event-application-planning-record-field')),
        findsOneWidget,
      );
    },
  );

  testWidgets('tapping a day with shifts opens day details', (tester) async {
    final backend = _ScheduleBackend(
      schedules: [
        _schedule(
          id: 'a',
          scheduleDate: DateTime(2026, 4, 2),
          workStart: DateTime(2026, 4, 2, 8),
          workEnd: DateTime(2026, 4, 2, 16),
        ),
      ],
    );
    final controller = await _buildAuthenticatedController(backend);

    await tester.pumpWidget(
      _buildHarness(controller: controller, backend: backend),
    );
    await tester.pumpAndSettle();

    await tester.tap(
      find.byKey(const ValueKey('schedule-calendar-day-2026-04-02')),
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('schedule-day-sheet-title')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('schedule-day-shift-a')), findsOneWidget);
  });

  testWidgets(
    'tapping a shift from day details opens existing shift detail sheet',
    (tester) async {
      final backend = _ScheduleBackend(
        schedules: [
          _schedule(
            id: 'a',
            scheduleDate: DateTime(2026, 4, 2),
            workStart: DateTime(2026, 4, 2, 8),
            workEnd: DateTime(2026, 4, 2, 16),
          ),
        ],
      );
      final controller = await _buildAuthenticatedController(backend);

      await tester.pumpWidget(
        _buildHarness(controller: controller, backend: backend),
      );
      await tester.pumpAndSettle();

      await tester.tap(
        find.byKey(const ValueKey('schedule-calendar-day-2026-04-02')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('schedule-day-shift-a')));
      await tester.pumpAndSettle();

      expect(find.text('Tagdienst'), findsOneWidget);
      expect(find.text('Route kopieren'), findsOneWidget);
      expect(find.text('Kalenderexport'), findsOneWidget);
      expect(find.text('Freigegebene Unterlagen'), findsOneWidget);
    },
  );
}
