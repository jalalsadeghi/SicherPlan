import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sicherplan_mobile/api/mobile_backend.dart';
import 'package:sicherplan_mobile/features/patrol/patrol_controller.dart';
import 'package:sicherplan_mobile/features/patrol/patrol_store.dart';

class _MemoryPatrolStore implements PatrolOfflineStore {
  StoredPatrolQueue? value;

  @override
  Future<void> clear() async {
    value = null;
  }

  @override
  Future<StoredPatrolQueue?> read() async => value;

  @override
  Future<void> write(StoredPatrolQueue queue) async {
    value = queue;
  }
}

class _FakePatrolBackend implements MobileBackendGateway {
  final routes = [
    PatrolAvailableRouteItem(
      shiftId: 'shift-1',
      planningRecordId: 'planning-1',
      patrolRouteId: 'route-1',
      routeNo: 'R-1',
      routeName: 'Night round',
      scheduleDate: DateTime.utc(2026, 4, 2),
      workStart: DateTime.utc(2026, 4, 2, 20, 0),
      workEnd: DateTime.utc(2026, 4, 3, 4, 0),
      meetingPoint: 'Gate A',
      locationLabel: 'Harbor North',
      checkpointCount: 2,
      checkpoints: const [
        PatrolCheckpointProgressItem(
          checkpointId: 'checkpoint-1',
          sequenceNo: 1,
          checkpointCode: 'CP-1',
          label: 'Gate',
          scanTypeCode: 'qr',
          minimumDwellSeconds: 0,
          isCompleted: false,
          lastEventAt: null,
        ),
        PatrolCheckpointProgressItem(
          checkpointId: 'checkpoint-2',
          sequenceNo: 2,
          checkpointCode: 'CP-2',
          label: 'Fence',
          scanTypeCode: 'nfc',
          minimumDwellSeconds: 0,
          isCompleted: false,
          lastEventAt: null,
        ),
      ],
    ),
  ];

  PatrolRoundItem? round;
  bool failNextCapture = false;
  int captureCalls = 0;

  @override
  Future<void> acknowledgeNotice(
    String accessToken,
    String tenantId,
    String noticeId, {
    String? acknowledgementText,
  }) async {}

  @override
  Future<PatrolRoundItem> abortPatrolRound(
    String accessToken,
    String patrolRoundId,
    PatrolRoundAbortPayload payload,
  ) async {
    final current = round!;
    final event = PatrolRoundEventItem(
      id: 'event-abort',
      patrolRoundId: current.id,
      sequenceNo: current.events.length + 1,
      checkpointId: null,
      occurredAt: payload.occurredAt ?? DateTime.now().toUtc(),
      eventTypeCode: 'round_aborted',
      scanMethodCode: 'manual',
      tokenValue: null,
      note: payload.note,
      reasonCode: payload.abortReasonCode,
      actorUserId: 'user-1',
      isPolicyCompliant: false,
      clientEventId: payload.clientEventId,
      attachmentDocumentIds: const [],
    );
    round = PatrolRoundItem(
      id: current.id,
      tenantId: current.tenantId,
      employeeId: current.employeeId,
      shiftId: current.shiftId,
      planningRecordId: current.planningRecordId,
      patrolRouteId: current.patrolRouteId,
      watchbookId: 'watchbook-1',
      summaryDocumentId: 'document-1',
      offlineSyncToken: current.offlineSyncToken,
      roundStatusCode: 'aborted',
      startedAt: current.startedAt,
      completedAt: null,
      abortedAt: event.occurredAt,
      abortReasonCode: payload.abortReasonCode,
      completionNote: payload.note,
      totalCheckpointCount: current.totalCheckpointCount,
      completedCheckpointCount: current.completedCheckpointCount,
      versionNo: current.versionNo + 1,
      events: [...current.events, event],
      checkpoints: current.checkpoints,
    );
    return round!;
  }

  @override
  Future<PatrolRoundItem> capturePatrolCheckpoint(
    String accessToken,
    String patrolRoundId,
    PatrolRoundCapturePayload payload,
  ) async {
    captureCalls += 1;
    if (failNextCapture) {
      failNextCapture = false;
      throw const MobileApiException(
        statusCode: 503,
        messageKey: 'errors.platform.internal',
      );
    }
    final current = round!;
    final scanned =
        payload.scanMethodCode == 'manual' || payload.tokenValue != null;
    final event = PatrolRoundEventItem(
      id: 'event-$captureCalls',
      patrolRoundId: current.id,
      sequenceNo: current.events.length + 1,
      checkpointId: payload.checkpointId,
      occurredAt: payload.occurredAt ?? DateTime.now().toUtc(),
      eventTypeCode: scanned ? 'checkpoint_scanned' : 'checkpoint_exception',
      scanMethodCode: payload.scanMethodCode,
      tokenValue: payload.tokenValue,
      note: payload.note,
      reasonCode: payload.reasonCode,
      actorUserId: 'user-1',
      isPolicyCompliant: scanned,
      clientEventId: payload.clientEventId,
      attachmentDocumentIds: const [],
    );
    final completedIds = <String>{
      for (final item in current.events)
        if (item.eventTypeCode == 'checkpoint_scanned' &&
            item.checkpointId != null)
          item.checkpointId!,
      if (scanned && payload.checkpointId != null) payload.checkpointId!,
    };
    round = PatrolRoundItem(
      id: current.id,
      tenantId: current.tenantId,
      employeeId: current.employeeId,
      shiftId: current.shiftId,
      planningRecordId: current.planningRecordId,
      patrolRouteId: current.patrolRouteId,
      watchbookId: current.watchbookId,
      summaryDocumentId: current.summaryDocumentId,
      offlineSyncToken: current.offlineSyncToken,
      roundStatusCode: current.roundStatusCode,
      startedAt: current.startedAt,
      completedAt: current.completedAt,
      abortedAt: current.abortedAt,
      abortReasonCode: current.abortReasonCode,
      completionNote: current.completionNote,
      totalCheckpointCount: current.totalCheckpointCount,
      completedCheckpointCount: completedIds.length,
      versionNo: current.versionNo + 1,
      events: [...current.events, event],
      checkpoints: current.checkpoints
          .map(
            (item) => PatrolCheckpointProgressItem(
              checkpointId: item.checkpointId,
              sequenceNo: item.sequenceNo,
              checkpointCode: item.checkpointCode,
              label: item.label,
              scanTypeCode: item.scanTypeCode,
              minimumDwellSeconds: item.minimumDwellSeconds,
              isCompleted: completedIds.contains(item.checkpointId),
              lastEventAt: item.checkpointId == payload.checkpointId
                  ? event.occurredAt
                  : item.lastEventAt,
            ),
          )
          .toList(),
    );
    return round!;
  }

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
  Future<TimeCaptureEventItem> captureOwnTimeEvent(
    String accessToken, {
    required String sourceChannelCode,
    required TimeCapturePayload payload,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<PatrolRoundItem> completePatrolRound(
    String accessToken,
    String patrolRoundId,
    PatrolRoundCompletePayload payload,
  ) async {
    final current = round!;
    final event = PatrolRoundEventItem(
      id: 'event-complete',
      patrolRoundId: current.id,
      sequenceNo: current.events.length + 1,
      checkpointId: null,
      occurredAt: payload.occurredAt ?? DateTime.now().toUtc(),
      eventTypeCode: 'round_completed',
      scanMethodCode: 'system',
      tokenValue: null,
      note: payload.note,
      reasonCode: null,
      actorUserId: 'user-1',
      isPolicyCompliant: true,
      clientEventId: payload.clientEventId,
      attachmentDocumentIds: const [],
    );
    round = PatrolRoundItem(
      id: current.id,
      tenantId: current.tenantId,
      employeeId: current.employeeId,
      shiftId: current.shiftId,
      planningRecordId: current.planningRecordId,
      patrolRouteId: current.patrolRouteId,
      watchbookId: 'watchbook-1',
      summaryDocumentId: 'document-1',
      offlineSyncToken: current.offlineSyncToken,
      roundStatusCode: 'completed',
      startedAt: current.startedAt,
      completedAt: event.occurredAt,
      abortedAt: null,
      abortReasonCode: null,
      completionNote: payload.note,
      totalCheckpointCount: current.totalCheckpointCount,
      completedCheckpointCount: current.completedCheckpointCount,
      versionNo: current.versionNo + 1,
      events: [...current.events, event],
      checkpoints: current.checkpoints,
    );
    return round!;
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
  Future<WatchbookEntryItem> createWatchbookEntry(
    String accessToken, {
    required String tenantId,
    required String watchbookId,
    required String entryTypeCode,
    required String narrative,
    String? trafficLightCode,
  }) {
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
  Future<EmployeeMobileContext> fetchMobileContext(String accessToken) {
    throw UnimplementedError();
  }

  @override
  Future<NoticeItem> fetchNotice(
    String accessToken,
    String tenantId,
    String noticeId,
  ) {
    throw UnimplementedError();
  }

  @override
  Future<NoticeFeedStatus> fetchNoticeFeedStatus(
    String accessToken,
    String tenantId,
  ) {
    throw UnimplementedError();
  }

  @override
  Future<List<NoticeItem>> fetchNotices(
    String accessToken,
    String tenantId,
  ) async => const [];

  @override
  Future<List<EmployeeEventApplicationItem>> fetchEventApplications(
    String accessToken,
  ) async => const [];

  @override
  Future<PatrolRoundItem?> fetchActivePatrolRound(String accessToken) async =>
      round?.roundStatusCode == 'active' ? round : null;

  @override
  Future<PatrolEvaluationItem> fetchPatrolEvaluation(
    String accessToken,
    String patrolRoundId,
  ) async {
    final current = round!;
    return PatrolEvaluationItem(
      patrolRoundId: current.id,
      tenantId: current.tenantId,
      employeeId: current.employeeId,
      patrolRouteId: current.patrolRouteId,
      roundStatusCode: current.roundStatusCode,
      totalCheckpointCount: current.totalCheckpointCount,
      completedCheckpointCount: current.completedCheckpointCount,
      exceptionCount: current.events
          .where((item) => item.eventTypeCode == 'checkpoint_exception')
          .length,
      manualCaptureCount: current.events
          .where((item) => item.scanMethodCode == 'manual')
          .length,
      mismatchCount: 0,
      watchbookId: current.watchbookId,
      summaryDocument: const EmployeeReleasedDocument(
        documentId: 'document-1',
        title: 'Patrol Summary',
        fileName: 'patrol.pdf',
        contentType: 'application/pdf',
        currentVersionNo: 1,
        relationType: 'summary_pdf',
      ),
      completionRatio: current.totalCheckpointCount == 0
          ? 1
          : current.completedCheckpointCount / current.totalCheckpointCount,
      complianceStatusCode: current.roundStatusCode == 'completed'
          ? 'compliant'
          : 'attention_required',
    );
  }

  @override
  Future<List<PatrolAvailableRouteItem>> fetchPatrolRoutes(
    String accessToken,
  ) async => routes;

  @override
  Future<PatrolRoundItem> fetchPatrolRound(
    String accessToken,
    String patrolRoundId,
  ) async => round!;

  @override
  Future<List<EmployeeReleasedScheduleItem>> fetchReleasedSchedules(
    String accessToken,
  ) async => const [];

  @override
  Future<List<TimeCaptureEventItem>> fetchTimeEvents(
    String accessToken,
  ) async => const [];

  @override
  Future<List<WatchbookListItem>> fetchWatchbooks(
    String accessToken,
    String tenantId,
  ) async => const [];

  @override
  Future<WatchbookReadModel> fetchWatchbook(
    String accessToken, {
    required String tenantId,
    required String watchbookId,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<(MobileCurrentUser, MobileAuthTokens)> login(
    MobileLoginPayload payload,
  ) {
    throw UnimplementedError();
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
  }) {
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
  ) {
    throw UnimplementedError();
  }

  @override
  Future<PatrolRoundItem> startPatrolRound(
    String accessToken,
    PatrolRoundStartPayload payload,
  ) async {
    round = PatrolRoundItem(
      id: 'round-1',
      tenantId: 'tenant-1',
      employeeId: 'employee-1',
      shiftId: payload.shiftId,
      planningRecordId: 'planning-1',
      patrolRouteId: payload.patrolRouteId,
      watchbookId: null,
      summaryDocumentId: null,
      offlineSyncToken: payload.offlineSyncToken,
      roundStatusCode: 'active',
      startedAt: DateTime.utc(2026, 4, 2, 20, 0),
      completedAt: null,
      abortedAt: null,
      abortReasonCode: null,
      completionNote: null,
      totalCheckpointCount: 2,
      completedCheckpointCount: 0,
      versionNo: 1,
      events: const [],
      checkpoints: routes.first.checkpoints,
    );
    return round!;
  }
}

void main() {
  test('offline patrol queue survives restart and syncs later', () async {
    final store = _MemoryPatrolStore();
    final backend = _FakePatrolBackend();
    final controller = PatrolController(
      backend: backend,
      store: store,
      withAccessToken: (action) => action('token'),
    );

    await controller.load();
    await controller.startRound(backend.routes.first);
    await controller.captureCheckpoint(
      checkpoint: backend.routes.first.checkpoints.first,
      scanMethodCode: 'qr',
      tokenValue: 'qr-1',
      note: 'Checkpoint reached.',
    );

    expect(store.value, isNotNull);
    expect(controller.activeRound?.completedCheckpointCount, 1);

    final reloaded = PatrolController(
      backend: backend,
      store: store,
      withAccessToken: (action) => action('token'),
    );
    await reloaded.load();

    expect(reloaded.activeRound, isNotNull);
    expect(reloaded.pendingOperationCount, 0);
    expect(reloaded.activeRound?.completedCheckpointCount, 1);
  });

  test('partial sync failure keeps remaining operations queued', () async {
    final store = _MemoryPatrolStore();
    final backend = _FakePatrolBackend()..failNextCapture = true;
    final controller = PatrolController(
      backend: backend,
      store: store,
      withAccessToken: (action) => action('token'),
    );

    await controller.load();
    await controller.startRound(backend.routes.first);
    await controller.captureCheckpoint(
      checkpoint: backend.routes.first.checkpoints.first,
      scanMethodCode: 'qr',
      tokenValue: 'qr-1',
      note: 'First checkpoint.',
    );

    expect(controller.pendingOperationCount, 1);
    expect(store.value, isNotNull);

    await controller.sync();

    expect(controller.pendingOperationCount, 0);
    expect(controller.activeRound?.completedCheckpointCount, 1);
  });

  test('complete round clears queue and loads evaluation', () async {
    final store = _MemoryPatrolStore();
    final backend = _FakePatrolBackend();
    final controller = PatrolController(
      backend: backend,
      store: store,
      withAccessToken: (action) => action('token'),
    );

    await controller.load();
    await controller.startRound(backend.routes.first);
    await controller.captureCheckpoint(
      checkpoint: backend.routes.first.checkpoints.first,
      scanMethodCode: 'qr',
      tokenValue: 'qr-1',
      note: 'First checkpoint.',
    );
    await controller.captureCheckpoint(
      checkpoint: backend.routes.first.checkpoints.last,
      scanMethodCode: 'manual',
      note: 'Manual fallback.',
      reasonCode: 'manual_fallback',
      attachments: [
        PatrolEvidenceAttachmentPayload(
          title: 'manual-note',
          fileName: 'manual.txt',
          contentType: 'text/plain',
          contentBase64: base64Encode(utf8.encode('manual evidence')),
        ),
      ],
    );
    await controller.completeRound(note: 'Round completed.');

    expect(controller.evaluation, isNotNull);
    expect(controller.evaluation?.complianceStatusCode, 'compliant');
    expect(store.value, isNull);
  });
}
