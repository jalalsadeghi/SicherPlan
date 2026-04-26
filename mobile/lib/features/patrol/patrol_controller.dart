import 'dart:math';

import 'package:flutter/foundation.dart';

import '../../api/mobile_backend.dart';
import 'patrol_store.dart';

class PatrolController extends ChangeNotifier {
  PatrolController({
    required MobileBackendGateway backend,
    required PatrolOfflineStore store,
    required Future<dynamic> Function(
      Future<dynamic> Function(String accessToken) action,
    )
    withAccessToken,
  }) : _backend = backend,
       _store = store,
       _withAccessToken = withAccessToken;

  final MobileBackendGateway _backend;
  final PatrolOfflineStore _store;
  final Future<dynamic> Function(
    Future<dynamic> Function(String accessToken) action,
  )
  _withAccessToken;

  List<PatrolAvailableRouteItem> _routes = const [];
  PatrolRoundItem? _activeRound;
  PatrolAvailableRouteItem? _activeRoute;
  PatrolEvaluationItem? _evaluation;
  StoredPatrolQueue? _queue;
  String? _messageKey;
  bool _loading = false;
  bool _syncing = false;

  List<PatrolAvailableRouteItem> get routes => _routes;
  PatrolRoundItem? get activeRound => _activeRound;
  PatrolAvailableRouteItem? get activeRoute => _activeRoute;
  PatrolEvaluationItem? get evaluation => _evaluation;
  String? get messageKey => _messageKey;
  bool get loading => _loading;
  bool get syncing => _syncing;
  int get pendingOperationCount => _queue?.pendingOperations.length ?? 0;
  bool get hasOfflineRound => _queue != null;

  Future<void> load() async {
    _loading = true;
    notifyListeners();
    _queue = await _store.read();
    if (_queue != null) {
      _activeRound = _queue!.localRound;
      _activeRoute = _queue!.route;
    }
    try {
      final serverRoutes = await _authorized(_backend.fetchPatrolRoutes);
      final serverRound = await _authorized(_backend.fetchActivePatrolRound);
      _routes = serverRoutes;
      if (serverRound != null) {
        _activeRound = serverRound;
        _activeRoute =
            _routeForRound(serverRoutes, serverRound) ?? _activeRoute;
        _evaluation = null;
        if (_queue != null &&
            _queue!.startPayload.offlineSyncToken ==
                serverRound.offlineSyncToken &&
            _queue!.pendingOperations.isEmpty) {
          _queue = null;
          await _store.clear();
        }
      } else if (_queue == null) {
        _activeRound = null;
        _activeRoute = null;
        _evaluation = null;
      }
      _messageKey = null;
    } catch (error) {
      _messageKey = _extractMessageKey(error);
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> startRound(PatrolAvailableRouteItem route) async {
    final syncToken = _buildId('round');
    final startPayload = PatrolRoundStartPayload(
      shiftId: route.shiftId,
      patrolRouteId: route.patrolRouteId,
      offlineSyncToken: syncToken,
    );
    final localRound = PatrolRoundItem(
      id: 'local-$syncToken',
      tenantId: '',
      employeeId: '',
      shiftId: route.shiftId,
      planningRecordId: route.planningRecordId,
      patrolRouteId: route.patrolRouteId,
      watchbookId: null,
      summaryDocumentId: null,
      offlineSyncToken: syncToken,
      roundStatusCode: 'active',
      startedAt: DateTime.now().toUtc(),
      completedAt: null,
      abortedAt: null,
      abortReasonCode: null,
      completionNote: null,
      totalCheckpointCount: route.checkpointCount,
      completedCheckpointCount: 0,
      versionNo: 1,
      events: const [],
      checkpoints: route.checkpoints,
    );
    _queue = StoredPatrolQueue(
      route: route,
      startPayload: startPayload,
      localRound: localRound,
      pendingOperations: const [],
    );
    _activeRoute = route;
    _activeRound = localRound;
    _evaluation = null;
    _messageKey = null;
    await _store.write(_queue!);
    notifyListeners();
    await sync();
  }

  Future<void> captureCheckpoint({
    required PatrolCheckpointProgressItem checkpoint,
    required String scanMethodCode,
    String? tokenValue,
    String? note,
    String? reasonCode,
    List<PatrolEvidenceAttachmentPayload> attachments = const [],
  }) async {
    final queue = _requireQueue();
    final sequenceNo = _nextLocalSequenceNo(queue);
    final payload = PatrolRoundCapturePayload(
      checkpointId: checkpoint.checkpointId,
      scanMethodCode: scanMethodCode,
      tokenValue: tokenValue,
      note: note,
      reasonCode: reasonCode,
      clientEventId: _buildId('capture'),
      occurredAt: DateTime.now().toUtc(),
      offlineSequenceNo: sequenceNo,
      attachments: attachments,
    );
    final eventTypeCode =
        _isPolicyCompliant(checkpoint, scanMethodCode, tokenValue)
        ? 'checkpoint_scanned'
        : 'checkpoint_exception';
    final event = PatrolRoundEventItem(
      id: 'local-event-$sequenceNo',
      patrolRoundId: queue.localRound.id,
      sequenceNo: queue.localRound.events.length + 1,
      checkpointId: checkpoint.checkpointId,
      occurredAt: payload.occurredAt!,
      eventTypeCode: eventTypeCode,
      scanMethodCode: scanMethodCode,
      tokenValue: tokenValue,
      note: note,
      reasonCode: reasonCode,
      actorUserId: 'local',
      isPolicyCompliant: eventTypeCode == 'checkpoint_scanned',
      clientEventId: payload.clientEventId,
      attachmentDocumentIds: const [],
    );
    _queue = StoredPatrolQueue(
      route: queue.route,
      startPayload: queue.startPayload,
      localRound: _applyEvent(queue.localRound, queue.route, event),
      pendingOperations: [
        ...queue.pendingOperations,
        StoredPatrolOperation(
          type: 'capture',
          localSequenceNo: sequenceNo,
          capture: payload,
        ),
      ],
    );
    _activeRound = _queue!.localRound;
    await _store.write(_queue!);
    notifyListeners();
    await sync();
  }

  Future<void> completeRound({String? note}) async {
    final queue = _requireQueue();
    final sequenceNo = _nextLocalSequenceNo(queue);
    final payload = PatrolRoundCompletePayload(
      clientEventId: _buildId('complete'),
      note: note,
      occurredAt: DateTime.now().toUtc(),
      offlineSequenceNo: sequenceNo,
    );
    final event = PatrolRoundEventItem(
      id: 'local-event-$sequenceNo',
      patrolRoundId: queue.localRound.id,
      sequenceNo: queue.localRound.events.length + 1,
      checkpointId: null,
      occurredAt: payload.occurredAt!,
      eventTypeCode: 'round_completed',
      scanMethodCode: 'system',
      tokenValue: null,
      note: note,
      reasonCode: null,
      actorUserId: 'local',
      isPolicyCompliant:
          queue.localRound.completedCheckpointCount >=
          queue.localRound.totalCheckpointCount,
      clientEventId: payload.clientEventId,
      attachmentDocumentIds: const [],
    );
    _queue = StoredPatrolQueue(
      route: queue.route,
      startPayload: queue.startPayload,
      localRound: _finalizeLocalRound(
        queue.localRound,
        event,
        completed: true,
        note: note,
      ),
      pendingOperations: [
        ...queue.pendingOperations,
        StoredPatrolOperation(
          type: 'complete',
          localSequenceNo: sequenceNo,
          complete: payload,
        ),
      ],
    );
    _activeRound = _queue!.localRound;
    await _store.write(_queue!);
    notifyListeners();
    await sync();
  }

  Future<void> abortRound({
    required String abortReasonCode,
    String? note,
    List<PatrolEvidenceAttachmentPayload> attachments = const [],
  }) async {
    final queue = _requireQueue();
    final sequenceNo = _nextLocalSequenceNo(queue);
    final payload = PatrolRoundAbortPayload(
      abortReasonCode: abortReasonCode,
      clientEventId: _buildId('abort'),
      note: note,
      occurredAt: DateTime.now().toUtc(),
      offlineSequenceNo: sequenceNo,
      attachments: attachments,
    );
    final event = PatrolRoundEventItem(
      id: 'local-event-$sequenceNo',
      patrolRoundId: queue.localRound.id,
      sequenceNo: queue.localRound.events.length + 1,
      checkpointId: null,
      occurredAt: payload.occurredAt!,
      eventTypeCode: 'round_aborted',
      scanMethodCode: 'manual',
      tokenValue: null,
      note: note,
      reasonCode: abortReasonCode,
      actorUserId: 'local',
      isPolicyCompliant: false,
      clientEventId: payload.clientEventId,
      attachmentDocumentIds: const [],
    );
    _queue = StoredPatrolQueue(
      route: queue.route,
      startPayload: queue.startPayload,
      localRound: _finalizeLocalRound(
        queue.localRound,
        event,
        completed: false,
        note: note,
        abortReasonCode: abortReasonCode,
      ),
      pendingOperations: [
        ...queue.pendingOperations,
        StoredPatrolOperation(
          type: 'abort',
          localSequenceNo: sequenceNo,
          abort: payload,
        ),
      ],
    );
    _activeRound = _queue!.localRound;
    await _store.write(_queue!);
    notifyListeners();
    await sync();
  }

  Future<void> sync() async {
    final queue = _queue;
    if (queue == null || _syncing) {
      return;
    }
    _syncing = true;
    _messageKey = null;
    notifyListeners();
    try {
      PatrolRoundItem currentRound = queue.localRound;
      if (!currentRound.id.startsWith('local-')) {
        currentRound = await _authorized(
          (token) => _backend.fetchPatrolRound(token, currentRound.id),
        );
      } else {
        currentRound = await _authorized(
          (token) => _backend.startPatrolRound(token, queue.startPayload),
        );
      }
      var remaining = List<StoredPatrolOperation>.from(queue.pendingOperations)
        ..sort(
          (left, right) =>
              left.localSequenceNo.compareTo(right.localSequenceNo),
        );
      while (remaining.isNotEmpty) {
        final current = remaining.first;
        if (current.capture != null) {
          currentRound = await _authorized(
            (token) => _backend.capturePatrolCheckpoint(
              token,
              currentRound.id,
              current.capture!,
            ),
          );
        } else if (current.complete != null) {
          currentRound = await _authorized(
            (token) => _backend.completePatrolRound(
              token,
              currentRound.id,
              current.complete!,
            ),
          );
        } else if (current.abort != null) {
          currentRound = await _authorized(
            (token) => _backend.abortPatrolRound(
              token,
              currentRound.id,
              current.abort!,
            ),
          );
        }
        remaining = remaining.sublist(1);
        _queue = StoredPatrolQueue(
          route: queue.route,
          startPayload: queue.startPayload,
          localRound: currentRound,
          pendingOperations: remaining,
        );
        await _store.write(_queue!);
      }
      _activeRound = currentRound.roundStatusCode == 'active'
          ? currentRound
          : currentRound;
      _activeRoute = queue.route;
      _evaluation = currentRound.roundStatusCode == 'active'
          ? null
          : await _authorized(
              (token) => _backend.fetchPatrolEvaluation(token, currentRound.id),
            );
      if (remaining.isEmpty) {
        if (currentRound.roundStatusCode == 'active') {
          _queue = StoredPatrolQueue(
            route: queue.route,
            startPayload: queue.startPayload,
            localRound: currentRound,
            pendingOperations: const [],
          );
          await _store.write(_queue!);
        } else {
          _queue = null;
          await _store.clear();
        }
      }
    } catch (error) {
      _messageKey = _extractMessageKey(error);
    } finally {
      _syncing = false;
      notifyListeners();
    }
  }

  String _extractMessageKey(Object error) {
    if (error is MobileApiException) {
      return error.messageKey;
    }
    return 'errors.platform.internal';
  }

  Future<T> _authorized<T>(
    Future<T> Function(String accessToken) action,
  ) async {
    final result = await _withAccessToken((accessToken) => action(accessToken));
    return result as T;
  }

  StoredPatrolQueue _requireQueue() {
    final queue = _queue;
    if (queue == null) {
      throw StateError('No local patrol queue available.');
    }
    return queue;
  }

  PatrolAvailableRouteItem? _routeForRound(
    List<PatrolAvailableRouteItem> routes,
    PatrolRoundItem round,
  ) {
    for (final route in routes) {
      if (route.shiftId == round.shiftId &&
          route.patrolRouteId == round.patrolRouteId) {
        return route;
      }
    }
    return null;
  }

  int _nextLocalSequenceNo(StoredPatrolQueue queue) {
    if (queue.pendingOperations.isEmpty) {
      return 1;
    }
    return queue.pendingOperations
            .map((item) => item.localSequenceNo)
            .reduce(max) +
        1;
  }

  PatrolRoundItem _applyEvent(
    PatrolRoundItem round,
    PatrolAvailableRouteItem route,
    PatrolRoundEventItem event,
  ) {
    final completedCheckpointIds = <String>{
      for (final item in round.events)
        if (item.eventTypeCode == 'checkpoint_scanned' &&
            item.checkpointId != null)
          item.checkpointId!,
    };
    if (event.eventTypeCode == 'checkpoint_scanned' &&
        event.checkpointId != null) {
      completedCheckpointIds.add(event.checkpointId!);
    }
    final checkpoints = route.checkpoints
        .map(
          (item) => PatrolCheckpointProgressItem(
            checkpointId: item.checkpointId,
            sequenceNo: item.sequenceNo,
            checkpointCode: item.checkpointCode,
            label: item.label,
            scanTypeCode: item.scanTypeCode,
            minimumDwellSeconds: item.minimumDwellSeconds,
            isCompleted: completedCheckpointIds.contains(item.checkpointId),
            lastEventAt: event.checkpointId == item.checkpointId
                ? event.occurredAt
                : item.lastEventAt,
          ),
        )
        .toList();
    return PatrolRoundItem(
      id: round.id,
      tenantId: round.tenantId,
      employeeId: round.employeeId,
      shiftId: round.shiftId,
      planningRecordId: round.planningRecordId,
      patrolRouteId: round.patrolRouteId,
      watchbookId: round.watchbookId,
      summaryDocumentId: round.summaryDocumentId,
      offlineSyncToken: round.offlineSyncToken,
      roundStatusCode: round.roundStatusCode,
      startedAt: round.startedAt,
      completedAt: round.completedAt,
      abortedAt: round.abortedAt,
      abortReasonCode: round.abortReasonCode,
      completionNote: round.completionNote,
      totalCheckpointCount: round.totalCheckpointCount,
      completedCheckpointCount: completedCheckpointIds.length,
      versionNo: round.versionNo,
      events: [...round.events, event],
      checkpoints: checkpoints,
    );
  }

  PatrolRoundItem _finalizeLocalRound(
    PatrolRoundItem round,
    PatrolRoundEventItem event, {
    required bool completed,
    String? note,
    String? abortReasonCode,
  }) {
    return PatrolRoundItem(
      id: round.id,
      tenantId: round.tenantId,
      employeeId: round.employeeId,
      shiftId: round.shiftId,
      planningRecordId: round.planningRecordId,
      patrolRouteId: round.patrolRouteId,
      watchbookId: round.watchbookId,
      summaryDocumentId: round.summaryDocumentId,
      offlineSyncToken: round.offlineSyncToken,
      roundStatusCode: completed ? 'completed' : 'aborted',
      startedAt: round.startedAt,
      completedAt: completed ? event.occurredAt : null,
      abortedAt: completed ? null : event.occurredAt,
      abortReasonCode: abortReasonCode,
      completionNote: note,
      totalCheckpointCount: round.totalCheckpointCount,
      completedCheckpointCount: round.completedCheckpointCount,
      versionNo: round.versionNo,
      events: [...round.events, event],
      checkpoints: round.checkpoints,
    );
  }

  bool _isPolicyCompliant(
    PatrolCheckpointProgressItem checkpoint,
    String scanMethodCode,
    String? tokenValue,
  ) {
    if (scanMethodCode == 'manual') {
      return true;
    }
    if (scanMethodCode != checkpoint.scanTypeCode) {
      return false;
    }
    return tokenValue != null && tokenValue.trim().isNotEmpty;
  }

  String _buildId(String prefix) {
    final now = DateTime.now().toUtc().microsecondsSinceEpoch;
    return '$prefix-$now-${Random().nextInt(999999)}';
  }
}
