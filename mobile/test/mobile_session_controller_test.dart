import 'package:flutter_test/flutter_test.dart';
import 'package:sicherplan_mobile/api/mobile_backend.dart';
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

class _FakeBackend implements MobileBackendGateway {
  _FakeBackend({this.loginError, this.restoreError, this.contextOverride});

  final MobileApiException? loginError;
  final MobileApiException? restoreError;
  final EmployeeMobileContext? contextOverride;

  final user = const MobileCurrentUser(
    id: 'user-1',
    tenantId: 'tenant-1',
    username: 'sysadmin',
    fullName: 'Sys Admin',
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
  }) {
    throw UnimplementedError();
  }

  @override
  Future<EmployeeEventApplicationItem> createEventApplication(
    String accessToken, {
    required String planningRecordId,
    String? note,
  }) {
    throw UnimplementedError();
  }

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
  Future<List<TimeCaptureEventItem>> fetchTimeEvents(
    String accessToken,
  ) async => const [];

  @override
  Future<WatchbookEntryItem> createWatchbookEntry(
    String accessToken, {
    required String tenantId,
    required String watchbookId,
    required String entryTypeCode,
    required String narrative,
    String? trafficLightCode,
  }) async => throw UnimplementedError();

  @override
  Future<PatrolRoundItem> abortPatrolRound(
    String accessToken,
    String patrolRoundId,
    PatrolRoundAbortPayload payload,
  ) {
    throw UnimplementedError();
  }

  @override
  Future<PatrolRoundItem> capturePatrolCheckpoint(
    String accessToken,
    String patrolRoundId,
    PatrolRoundCapturePayload payload,
  ) {
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
  Future<EmployeeMobileContext> fetchMobileContext(String accessToken) async {
    return contextOverride ??
        const EmployeeMobileContext(
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
          hasPatrolAccess: true,
        );
  }

  @override
  Future<List<EmployeeEventApplicationItem>> fetchEventApplications(
    String accessToken,
  ) async => const [];

  @override
  Future<NoticeItem> fetchNotice(
    String accessToken,
    String tenantId,
    String noticeId,
  ) async => const NoticeItem(
    id: 'notice-1',
    title: 'Notice',
    summary: null,
    languageCode: 'de',
    mandatoryAcknowledgement: false,
    status: 'published',
    acknowledgedAt: null,
    attachmentDocumentIds: <String>[],
    attachments: <NoticeAttachmentItem>[],
    links: <NoticeLinkItem>[],
    openedAt: null,
  );

  @override
  Future<NoticeFeedStatus> fetchNoticeFeedStatus(
    String accessToken,
    String tenantId,
  ) async => const NoticeFeedStatus(
    totalCount: 0,
    unreadCount: 0,
    mandatoryUnacknowledgedCount: 0,
    blockingRequired: false,
  );

  @override
  Future<List<NoticeItem>> fetchNotices(
    String accessToken,
    String tenantId,
  ) async => const [];

  @override
  Future<List<EmployeeReleasedScheduleItem>> fetchReleasedSchedules(
    String accessToken,
  ) async => const [];

  @override
  Future<WatchbookReadModel> fetchWatchbook(
    String accessToken, {
    required String tenantId,
    required String watchbookId,
  }) async => WatchbookReadModel(
    id: 'watchbook-1',
    contextType: 'site',
    logDate: DateTime.utc(2026, 1, 1),
    headline: null,
    summary: null,
    reviewStatusCode: 'pending',
    closureStateCode: 'open',
    entries: <WatchbookEntryItem>[],
  );

  @override
  Future<PatrolRoundItem?> fetchActivePatrolRound(String accessToken) async =>
      null;

  @override
  Future<PatrolEvaluationItem> fetchPatrolEvaluation(
    String accessToken,
    String patrolRoundId,
  ) {
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
  ) {
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
  ) async {
    if (loginError != null) {
      throw loginError!;
    }
    return (user, tokens);
  }

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
  }) async => WatchbookReadModel(
    id: 'watchbook-1',
    contextType: 'site',
    logDate: DateTime.utc(2026, 1, 1),
    headline: null,
    summary: null,
    reviewStatusCode: 'pending',
    closureStateCode: 'open',
    entries: <WatchbookEntryItem>[],
  );

  @override
  Future<PatrolRoundItem> startPatrolRound(
    String accessToken,
    PatrolRoundStartPayload payload,
  ) {
    throw UnimplementedError();
  }

  @override
  Future<TimeCaptureEventItem> captureOwnTimeEvent(
    String accessToken, {
    required String sourceChannelCode,
    required TimeCapturePayload payload,
  }) async => TimeCaptureEventItem(
    id: 'time-event-1',
    actorTypeCode: 'employee',
    employeeId: 'employee-1',
    subcontractorWorkerId: null,
    shiftId: payload.shiftId,
    assignmentId: null,
    sourceChannelCode: sourceChannelCode,
    eventCode: payload.eventCode,
    occurredAt: payload.occurredAt ?? DateTime.utc(2026, 1, 1, 8),
    deviceId: null,
    validationStatusCode: 'accepted',
    validationMessageKey: null,
    rawTokenSuffix: null,
  );

  @override
  Future<PatrolRoundItem> completePatrolRound(
    String accessToken,
    String patrolRoundId,
    PatrolRoundCompletePayload payload,
  ) {
    throw UnimplementedError();
  }

  @override
  Future<EmployeeReleasedScheduleItem> respondToAssignment(
    String accessToken, {
    required String assignmentId,
    required String responseCode,
    required int? versionNo,
    String? note,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<(MobileCurrentUser, MobileAuthTokens)> restore(
    MobileAuthTokens tokens,
  ) async {
    if (restoreError != null) {
      throw restoreError!;
    }
    return (user, this.tokens);
  }
}

void main() {
  test('bootstrap without stored session becomes unauthenticated', () async {
    final controller = MobileSessionController(
      backend: _FakeBackend(),
      store: _MemoryStore(),
    );
    await controller.bootstrap();
    expect(controller.phase, MobileSessionPhase.unauthenticated);
  });

  test('login stores authenticated employee session', () async {
    final store = _MemoryStore();
    final controller = MobileSessionController(
      backend: _FakeBackend(),
      store: store,
    );
    await controller.login(
      tenantCode: 'tenant-1',
      identifier: 'sysadmin',
      password: 'secret',
      deviceLabel: 'flutter',
      deviceId: 'device-1',
    );
    expect(controller.phase, MobileSessionPhase.authenticated);
    expect(store.value?.context.employeeId, 'employee-1');
  });

  test('wrong mobile role is rejected during bootstrap', () async {
    final store = _MemoryStore();
    store.value = StoredMobileSession(
      tokens: const MobileAuthTokens(
        accessToken: 'a',
        refreshToken: 'r',
        sessionId: 's',
      ),
      user: const MobileCurrentUser(
        id: 'user-1',
        tenantId: 'tenant-1',
        username: 'x',
        fullName: 'X',
        locale: 'de',
        timezone: 'Europe/Berlin',
        roleKeys: ['tenant_admin'],
        permissionKeys: ['portal.employee.access'],
      ),
      context: const EmployeeMobileContext(
        tenantId: 'tenant-1',
        tenantCode: 'nord',
        tenantName: 'SicherPlan Nord',
        photoDocumentId: null,
        photoCurrentVersionNo: null,
        photoContentType: null,
        userId: 'user-1',
        employeeId: 'employee-1',
        personnelNo: 'EMP-1',
        fullName: 'X',
        preferredName: null,
        workEmail: null,
        mobilePhone: null,
        defaultBranchId: null,
        defaultMandateId: null,
        locale: 'de',
        timezone: 'Europe/Berlin',
        appRole: 'employee',
        roleKeys: ['tenant_admin'],
        hasScheduleAccess: true,
        hasDocumentAccess: true,
        hasNoticeAccess: true,
        hasTimeCaptureAccess: true,
        hasWatchbookAccess: true,
        hasPatrolAccess: true,
      ),
    );
    final controller = MobileSessionController(
      backend: _FakeBackend(
        contextOverride: const EmployeeMobileContext(
          tenantId: 'tenant-1',
          tenantCode: 'nord',
          tenantName: 'SicherPlan Nord',
          photoDocumentId: null,
          photoCurrentVersionNo: null,
          photoContentType: null,
          userId: 'user-1',
          employeeId: 'employee-1',
          personnelNo: 'EMP-1',
          fullName: 'X',
          preferredName: null,
          workEmail: null,
          mobilePhone: null,
          defaultBranchId: null,
          defaultMandateId: null,
          locale: 'de',
          timezone: 'Europe/Berlin',
          appRole: 'employee',
          roleKeys: ['tenant_admin'],
          hasScheduleAccess: true,
          hasDocumentAccess: true,
          hasNoticeAccess: true,
          hasTimeCaptureAccess: true,
          hasWatchbookAccess: true,
          hasPatrolAccess: true,
        ),
      ),
      store: store,
    );
    await controller.bootstrap();
    expect(controller.phase, MobileSessionPhase.forbidden);
  });

  test('invalid stored session clears back to unauthenticated', () async {
    final store = _MemoryStore();
    store.value = StoredMobileSession(
      tokens: const MobileAuthTokens(
        accessToken: 'a',
        refreshToken: 'r',
        sessionId: 's',
      ),
      user: const MobileCurrentUser(
        id: 'user-1',
        tenantId: 'tenant-1',
        username: 'x',
        fullName: 'X',
        locale: 'de',
        timezone: 'Europe/Berlin',
        roleKeys: ['employee_user'],
        permissionKeys: ['portal.employee.access'],
      ),
      context: const EmployeeMobileContext(
        tenantId: 'tenant-1',
        tenantCode: 'nord',
        tenantName: 'SicherPlan Nord',
        photoDocumentId: null,
        photoCurrentVersionNo: null,
        photoContentType: null,
        userId: 'user-1',
        employeeId: 'employee-1',
        personnelNo: 'EMP-1',
        fullName: 'X',
        preferredName: null,
        workEmail: null,
        mobilePhone: null,
        defaultBranchId: null,
        defaultMandateId: null,
        locale: 'de',
        timezone: 'Europe/Berlin',
        appRole: 'employee',
        roleKeys: ['employee_user'],
        hasScheduleAccess: true,
        hasDocumentAccess: true,
        hasNoticeAccess: true,
        hasTimeCaptureAccess: true,
        hasWatchbookAccess: true,
        hasPatrolAccess: true,
      ),
    );
    final controller = MobileSessionController(
      backend: _FakeBackend(
        restoreError: const MobileApiException(
          statusCode: 401,
          messageKey: 'errors.iam.auth.invalid_access_token',
        ),
      ),
      store: store,
    );
    await controller.bootstrap();
    expect(controller.phase, MobileSessionPhase.unauthenticated);
    expect(store.value, isNull);
  });

  test('login surfaces invalid credentials as unauthenticated state', () async {
    final controller = MobileSessionController(
      backend: _FakeBackend(
        loginError: const MobileApiException(
          statusCode: 401,
          messageKey: 'errors.iam.auth.invalid_credentials',
        ),
      ),
      store: _MemoryStore(),
    );
    await controller.login(
      tenantCode: 'tenant-1',
      identifier: 'sysadmin',
      password: 'bad',
      deviceLabel: 'flutter',
      deviceId: 'device-1',
    );
    expect(controller.phase, MobileSessionPhase.unauthenticated);
    expect(controller.messageKey, 'errors.iam.auth.invalid_credentials');
  });
}
