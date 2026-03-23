import 'dart:convert';
import 'dart:io';

import '../../api/mobile_backend.dart';

class StoredPatrolOperation {
  const StoredPatrolOperation({
    required this.type,
    required this.localSequenceNo,
    this.capture,
    this.complete,
    this.abort,
  });

  final String type;
  final int localSequenceNo;
  final PatrolRoundCapturePayload? capture;
  final PatrolRoundCompletePayload? complete;
  final PatrolRoundAbortPayload? abort;

  Map<String, dynamic> toJson() => {
    'type': type,
    'local_sequence_no': localSequenceNo,
    'capture': capture?.toJson(),
    'complete': complete?.toJson(),
    'abort': abort?.toJson(),
  };

  factory StoredPatrolOperation.fromJson(Map<String, dynamic> json) {
    PatrolRoundCapturePayload? capture;
    PatrolRoundCompletePayload? complete;
    PatrolRoundAbortPayload? abort;
    final captureJson = json['capture'];
    if (captureJson is Map) {
      final item = captureJson.cast<String, dynamic>();
      capture = PatrolRoundCapturePayload(
        checkpointId: item['checkpoint_id'] as String?,
        scanMethodCode: item['scan_method_code'] as String,
        tokenValue: item['token_value'] as String?,
        latitude: (item['latitude'] as num?)?.toDouble(),
        longitude: (item['longitude'] as num?)?.toDouble(),
        note: item['note'] as String?,
        reasonCode: item['reason_code'] as String?,
        occurredAt: item['occurred_at'] != null ? DateTime.parse(item['occurred_at'] as String) : null,
        offlineSequenceNo: item['offline_sequence_no'] as int?,
        clientEventId: item['client_event_id'] as String,
        attachments: (item['attachments'] as List? ?? const [])
            .cast<Map<String, dynamic>>()
            .map(
              (attachment) => PatrolEvidenceAttachmentPayload(
                title: attachment['title'] as String?,
                fileName: attachment['file_name'] as String,
                contentType: attachment['content_type'] as String,
                contentBase64: attachment['content_base64'] as String,
              ),
            )
            .toList(),
      );
    }
    final completeJson = json['complete'];
    if (completeJson is Map) {
      final item = completeJson.cast<String, dynamic>();
      complete = PatrolRoundCompletePayload(
        clientEventId: item['client_event_id'] as String,
        note: item['note'] as String?,
        occurredAt: item['occurred_at'] != null ? DateTime.parse(item['occurred_at'] as String) : null,
        offlineSequenceNo: item['offline_sequence_no'] as int?,
      );
    }
    final abortJson = json['abort'];
    if (abortJson is Map) {
      final item = abortJson.cast<String, dynamic>();
      abort = PatrolRoundAbortPayload(
        abortReasonCode: item['abort_reason_code'] as String,
        clientEventId: item['client_event_id'] as String,
        note: item['note'] as String?,
        occurredAt: item['occurred_at'] != null ? DateTime.parse(item['occurred_at'] as String) : null,
        offlineSequenceNo: item['offline_sequence_no'] as int?,
        attachments: (item['attachments'] as List? ?? const [])
            .cast<Map<String, dynamic>>()
            .map(
              (attachment) => PatrolEvidenceAttachmentPayload(
                title: attachment['title'] as String?,
                fileName: attachment['file_name'] as String,
                contentType: attachment['content_type'] as String,
                contentBase64: attachment['content_base64'] as String,
              ),
            )
            .toList(),
      );
    }
    return StoredPatrolOperation(
      type: json['type'] as String,
      localSequenceNo: json['local_sequence_no'] as int? ?? 0,
      capture: capture,
      complete: complete,
      abort: abort,
    );
  }
}

class StoredPatrolQueue {
  const StoredPatrolQueue({
    required this.route,
    required this.startPayload,
    required this.localRound,
    required this.pendingOperations,
  });

  final PatrolAvailableRouteItem route;
  final PatrolRoundStartPayload startPayload;
  final PatrolRoundItem localRound;
  final List<StoredPatrolOperation> pendingOperations;

  Map<String, dynamic> toJson() => {
    'route': route.toJson(),
    'start_payload': startPayload.toJson(),
    'local_round': localRound.toJson(),
    'pending_operations': pendingOperations.map((item) => item.toJson()).toList(),
  };

  factory StoredPatrolQueue.fromJson(Map<String, dynamic> json) {
    final startPayload = (json['start_payload'] as Map).cast<String, dynamic>();
    return StoredPatrolQueue(
      route: PatrolAvailableRouteItem.fromJson((json['route'] as Map).cast<String, dynamic>()),
      startPayload: PatrolRoundStartPayload(
        shiftId: startPayload['shift_id'] as String,
        patrolRouteId: startPayload['patrol_route_id'] as String,
        offlineSyncToken: startPayload['offline_sync_token'] as String,
      ),
      localRound: PatrolRoundItem.fromJson((json['local_round'] as Map).cast<String, dynamic>()),
      pendingOperations: (json['pending_operations'] as List? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(StoredPatrolOperation.fromJson)
          .toList(),
    );
  }
}

abstract class PatrolOfflineStore {
  Future<StoredPatrolQueue?> read();
  Future<void> write(StoredPatrolQueue queue);
  Future<void> clear();
}

class FilePatrolOfflineStore implements PatrolOfflineStore {
  FilePatrolOfflineStore({String? filePath})
    : _file = File(filePath ?? '${Directory.systemTemp.path}/sicherplan_mobile_patrol_queue.json');

  final File _file;

  @override
  Future<StoredPatrolQueue?> read() async {
    if (!await _file.exists()) {
      return null;
    }
    final raw = await _file.readAsString();
    if (raw.trim().isEmpty) {
      return null;
    }
    return StoredPatrolQueue.fromJson((jsonDecode(raw) as Map).cast<String, dynamic>());
  }

  @override
  Future<void> write(StoredPatrolQueue queue) async {
    await _file.parent.create(recursive: true);
    await _file.writeAsString(jsonEncode(queue.toJson()), flush: true);
  }

  @override
  Future<void> clear() async {
    if (await _file.exists()) {
      await _file.delete();
    }
  }
}
