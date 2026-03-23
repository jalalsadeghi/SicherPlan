import 'dart:convert';
import 'dart:io';

import '../config/app_config.dart';

class MobileApiException implements Exception {
  const MobileApiException({
    required this.statusCode,
    required this.messageKey,
    this.body,
  });

  final int statusCode;
  final String messageKey;
  final Map<String, dynamic>? body;
}

class MobileLoginPayload {
  const MobileLoginPayload({
    required this.tenantCode,
    required this.identifier,
    required this.password,
    required this.deviceLabel,
    required this.deviceId,
  });

  final String tenantCode;
  final String identifier;
  final String password;
  final String deviceLabel;
  final String deviceId;
}

class MobileAuthTokens {
  const MobileAuthTokens({
    required this.accessToken,
    required this.refreshToken,
    required this.sessionId,
  });

  final String accessToken;
  final String refreshToken;
  final String sessionId;

  factory MobileAuthTokens.fromLogin(Map<String, dynamic> json) {
    final session = (json['session'] as Map).cast<String, dynamic>();
    return MobileAuthTokens(
      accessToken: session['access_token'] as String,
      refreshToken: session['refresh_token'] as String,
      sessionId: session['session_id'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'access_token': accessToken,
    'refresh_token': refreshToken,
    'session_id': sessionId,
  };

  factory MobileAuthTokens.fromJson(Map<String, dynamic> json) {
    return MobileAuthTokens(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      sessionId: json['session_id'] as String,
    );
  }
}

class MobileCurrentUser {
  const MobileCurrentUser({
    required this.id,
    required this.tenantId,
    required this.username,
    required this.fullName,
    required this.locale,
    required this.timezone,
    required this.roleKeys,
    required this.permissionKeys,
  });

  final String id;
  final String tenantId;
  final String username;
  final String fullName;
  final String locale;
  final String timezone;
  final List<String> roleKeys;
  final List<String> permissionKeys;

  factory MobileCurrentUser.fromAuthResponses(
    Map<String, dynamic> loginJson,
    Map<String, dynamic> codesJson,
  ) {
    final user = (loginJson['user'] as Map).cast<String, dynamic>();
    final roles = (user['roles'] as List? ?? const [])
        .cast<Map<String, dynamic>>()
        .map((item) => item['role_key'] as String)
        .toSet()
        .toList()
      ..sort();
    final permissions = (codesJson['items'] as List? ?? const [])
        .cast<String>()
        .toList()
      ..sort();
    return MobileCurrentUser(
      id: user['id'] as String,
      tenantId: user['tenant_id'] as String,
      username: user['username'] as String,
      fullName: user['full_name'] as String,
      locale: user['locale'] as String? ?? 'de',
      timezone: user['timezone'] as String? ?? 'Europe/Berlin',
      roleKeys: roles,
      permissionKeys: permissions,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'tenant_id': tenantId,
    'username': username,
    'full_name': fullName,
    'locale': locale,
    'timezone': timezone,
    'role_keys': roleKeys,
    'permission_keys': permissionKeys,
  };

  factory MobileCurrentUser.fromJson(Map<String, dynamic> json) {
    return MobileCurrentUser(
      id: json['id'] as String,
      tenantId: json['tenant_id'] as String,
      username: json['username'] as String,
      fullName: json['full_name'] as String,
      locale: json['locale'] as String,
      timezone: json['timezone'] as String,
      roleKeys: (json['role_keys'] as List).cast<String>(),
      permissionKeys: (json['permission_keys'] as List).cast<String>(),
    );
  }
}

class EmployeeMobileContext {
  const EmployeeMobileContext({
    required this.tenantId,
    required this.userId,
    required this.employeeId,
    required this.personnelNo,
    required this.fullName,
    required this.preferredName,
    required this.workEmail,
    required this.mobilePhone,
    required this.defaultBranchId,
    required this.defaultMandateId,
    required this.locale,
    required this.timezone,
    required this.appRole,
    required this.roleKeys,
    required this.hasScheduleAccess,
    required this.hasDocumentAccess,
    required this.hasNoticeAccess,
    required this.hasTimeCaptureAccess,
    required this.hasWatchbookAccess,
    required this.hasPatrolAccess,
  });

  final String tenantId;
  final String userId;
  final String employeeId;
  final String personnelNo;
  final String fullName;
  final String? preferredName;
  final String? workEmail;
  final String? mobilePhone;
  final String? defaultBranchId;
  final String? defaultMandateId;
  final String locale;
  final String timezone;
  final String appRole;
  final List<String> roleKeys;
  final bool hasScheduleAccess;
  final bool hasDocumentAccess;
  final bool hasNoticeAccess;
  final bool hasTimeCaptureAccess;
  final bool hasWatchbookAccess;
  final bool hasPatrolAccess;

  factory EmployeeMobileContext.fromJson(Map<String, dynamic> json) {
    return EmployeeMobileContext(
      tenantId: json['tenant_id'] as String,
      userId: json['user_id'] as String,
      employeeId: json['employee_id'] as String,
      personnelNo: json['personnel_no'] as String,
      fullName: json['full_name'] as String,
      preferredName: json['preferred_name'] as String?,
      workEmail: json['work_email'] as String?,
      mobilePhone: json['mobile_phone'] as String?,
      defaultBranchId: json['default_branch_id'] as String?,
      defaultMandateId: json['default_mandate_id'] as String?,
      locale: json['locale'] as String? ?? 'de',
      timezone: json['timezone'] as String? ?? 'Europe/Berlin',
      appRole: json['app_role'] as String? ?? 'employee',
      roleKeys: (json['role_keys'] as List? ?? const []).cast<String>(),
      hasScheduleAccess: json['has_schedule_access'] as bool? ?? true,
      hasDocumentAccess: json['has_document_access'] as bool? ?? true,
      hasNoticeAccess: json['has_notice_access'] as bool? ?? true,
      hasTimeCaptureAccess: json['has_time_capture_access'] as bool? ?? true,
      hasWatchbookAccess: json['has_watchbook_access'] as bool? ?? true,
      hasPatrolAccess: json['has_patrol_access'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() => {
    'tenant_id': tenantId,
    'user_id': userId,
    'employee_id': employeeId,
    'personnel_no': personnelNo,
    'full_name': fullName,
    'preferred_name': preferredName,
    'work_email': workEmail,
    'mobile_phone': mobilePhone,
    'default_branch_id': defaultBranchId,
    'default_mandate_id': defaultMandateId,
    'locale': locale,
    'timezone': timezone,
    'app_role': appRole,
    'role_keys': roleKeys,
    'has_schedule_access': hasScheduleAccess,
    'has_document_access': hasDocumentAccess,
    'has_notice_access': hasNoticeAccess,
    'has_time_capture_access': hasTimeCaptureAccess,
    'has_watchbook_access': hasWatchbookAccess,
    'has_patrol_access': hasPatrolAccess,
  };
}

class EmployeeReleasedDocument {
  const EmployeeReleasedDocument({
    required this.documentId,
    required this.title,
    required this.fileName,
    required this.contentType,
    required this.currentVersionNo,
    required this.relationType,
  });

  final String documentId;
  final String? fileName;
  final String? contentType;
  final int? currentVersionNo;
  final String relationType;
  final String title;

  factory EmployeeReleasedDocument.fromJson(Map<String, dynamic> json) {
    return EmployeeReleasedDocument(
      documentId: json['document_id'] as String,
      title: json['title'] as String,
      fileName: json['file_name'] as String?,
      contentType: json['content_type'] as String?,
      currentVersionNo: json['current_version_no'] as int?,
      relationType: json['relation_type'] as String? ?? 'deployment_output',
    );
  }
}

class EmployeeReleasedScheduleItem {
  const EmployeeReleasedScheduleItem({
    required this.id,
    required this.employeeId,
    required this.shiftId,
    required this.planningRecordId,
    required this.orderId,
    required this.siteId,
    required this.scheduleDate,
    required this.shiftLabel,
    required this.workStart,
    required this.workEnd,
    required this.locationLabel,
    required this.meetingPoint,
    required this.assignmentStatus,
    required this.confirmationStatus,
    required this.documents,
  });

  final String id;
  final String employeeId;
  final String shiftId;
  final String? planningRecordId;
  final String? orderId;
  final String? siteId;
  final DateTime scheduleDate;
  final String shiftLabel;
  final DateTime workStart;
  final DateTime workEnd;
  final String? locationLabel;
  final String? meetingPoint;
  final String assignmentStatus;
  final String confirmationStatus;
  final List<EmployeeReleasedDocument> documents;

  factory EmployeeReleasedScheduleItem.fromJson(Map<String, dynamic> json) {
    return EmployeeReleasedScheduleItem(
      id: json['id'] as String,
      employeeId: json['employee_id'] as String,
      shiftId: json['shift_id'] as String,
      planningRecordId: json['planning_record_id'] as String?,
      orderId: json['order_id'] as String?,
      siteId: json['site_id'] as String?,
      scheduleDate: DateTime.parse(json['schedule_date'] as String),
      shiftLabel: json['shift_label'] as String,
      workStart: DateTime.parse(json['work_start'] as String),
      workEnd: DateTime.parse(json['work_end'] as String),
      locationLabel: json['location_label'] as String?,
      meetingPoint: json['meeting_point'] as String?,
      assignmentStatus: json['assignment_status'] as String,
      confirmationStatus: json['confirmation_status'] as String,
      documents: (json['documents'] as List? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(EmployeeReleasedDocument.fromJson)
          .toList(),
    );
  }
}

class TimeCaptureEventItem {
  const TimeCaptureEventItem({
    required this.id,
    required this.actorTypeCode,
    required this.employeeId,
    required this.subcontractorWorkerId,
    required this.shiftId,
    required this.assignmentId,
    required this.sourceChannelCode,
    required this.eventCode,
    required this.occurredAt,
    required this.deviceId,
    required this.validationStatusCode,
    required this.validationMessageKey,
    required this.rawTokenSuffix,
  });

  final String id;
  final String actorTypeCode;
  final String? employeeId;
  final String? subcontractorWorkerId;
  final String? shiftId;
  final String? assignmentId;
  final String sourceChannelCode;
  final String eventCode;
  final DateTime occurredAt;
  final String? deviceId;
  final String validationStatusCode;
  final String? validationMessageKey;
  final String? rawTokenSuffix;

  factory TimeCaptureEventItem.fromJson(Map<String, dynamic> json) {
    return TimeCaptureEventItem(
      id: json['id'] as String,
      actorTypeCode: json['actor_type_code'] as String,
      employeeId: json['employee_id'] as String?,
      subcontractorWorkerId: json['subcontractor_worker_id'] as String?,
      shiftId: json['shift_id'] as String?,
      assignmentId: json['assignment_id'] as String?,
      sourceChannelCode: json['source_channel_code'] as String,
      eventCode: json['event_code'] as String,
      occurredAt: DateTime.parse(json['occurred_at'] as String),
      deviceId: json['device_id'] as String?,
      validationStatusCode: json['validation_status_code'] as String,
      validationMessageKey: json['validation_message_key'] as String?,
      rawTokenSuffix: json['raw_token_suffix'] as String?,
    );
  }
}

class TimeCapturePayload {
  const TimeCapturePayload({
    required this.shiftId,
    required this.eventCode,
    this.assignmentId,
    this.occurredAt,
    this.latitude,
    this.longitude,
    this.note,
    this.clientEventId,
    this.rawToken,
    this.scanMediumCode,
  });

  final String shiftId;
  final String eventCode;
  final String? assignmentId;
  final DateTime? occurredAt;
  final double? latitude;
  final double? longitude;
  final String? note;
  final String? clientEventId;
  final String? rawToken;
  final String? scanMediumCode;

  Map<String, dynamic> toJson() => {
    'shift_id': shiftId,
    'assignment_id': assignmentId,
    'event_code': eventCode,
    'occurred_at': occurredAt?.toIso8601String(),
    'latitude': latitude,
    'longitude': longitude,
    'note': note,
    'client_event_id': clientEventId,
    'raw_token': rawToken,
    'scan_medium_code': scanMediumCode,
  };
}

class EmployeeEventApplicationItem {
  const EmployeeEventApplicationItem({
    required this.id,
    required this.planningRecordId,
    required this.status,
    required this.note,
    required this.versionNo,
    required this.createdAt,
  });

  final String id;
  final String planningRecordId;
  final String status;
  final String? note;
  final int versionNo;
  final DateTime createdAt;

  factory EmployeeEventApplicationItem.fromJson(Map<String, dynamic> json) {
    return EmployeeEventApplicationItem(
      id: json['id'] as String,
      planningRecordId: json['planning_record_id'] as String,
      status: json['status'] as String,
      note: json['note'] as String?,
      versionNo: json['version_no'] as int? ?? 1,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class EmployeeMobileDocument {
  const EmployeeMobileDocument({
    required this.documentId,
    required this.ownerType,
    required this.ownerId,
    required this.relationType,
    required this.title,
    required this.fileName,
    required this.contentType,
    required this.currentVersionNo,
    required this.shiftId,
    required this.scheduleDate,
  });

  final String documentId;
  final String ownerType;
  final String ownerId;
  final String relationType;
  final String title;
  final String? fileName;
  final String? contentType;
  final int? currentVersionNo;
  final String? shiftId;
  final DateTime? scheduleDate;

  factory EmployeeMobileDocument.fromJson(Map<String, dynamic> json) {
    return EmployeeMobileDocument(
      documentId: json['document_id'] as String,
      ownerType: json['owner_type'] as String,
      ownerId: json['owner_id'] as String,
      relationType: json['relation_type'] as String,
      title: json['title'] as String,
      fileName: json['file_name'] as String?,
      contentType: json['content_type'] as String?,
      currentVersionNo: json['current_version_no'] as int?,
      shiftId: json['shift_id'] as String?,
      scheduleDate: json['schedule_date'] != null ? DateTime.parse(json['schedule_date'] as String) : null,
    );
  }
}

class EmployeeMobileCredential {
  const EmployeeMobileCredential({
    required this.credentialId,
    required this.credentialNo,
    required this.credentialType,
    required this.encodedValue,
    required this.validFrom,
    required this.validUntil,
    required this.status,
    required this.badgeDocumentId,
    required this.badgeFileName,
  });

  final String credentialId;
  final String credentialNo;
  final String credentialType;
  final String encodedValue;
  final DateTime validFrom;
  final DateTime? validUntil;
  final String status;
  final String? badgeDocumentId;
  final String? badgeFileName;

  factory EmployeeMobileCredential.fromJson(Map<String, dynamic> json) {
    return EmployeeMobileCredential(
      credentialId: json['credential_id'] as String,
      credentialNo: json['credential_no'] as String,
      credentialType: json['credential_type'] as String,
      encodedValue: json['encoded_value'] as String,
      validFrom: DateTime.parse(json['valid_from'] as String),
      validUntil: json['valid_until'] != null ? DateTime.parse(json['valid_until'] as String) : null,
      status: json['status'] as String,
      badgeDocumentId: json['badge_document_id'] as String?,
      badgeFileName: json['badge_file_name'] as String?,
    );
  }
}

class NoticeItem {
  const NoticeItem({
    required this.id,
    required this.title,
    required this.summary,
    required this.languageCode,
    required this.mandatoryAcknowledgement,
    required this.status,
    required this.acknowledgedAt,
    required this.attachmentDocumentIds,
    required this.attachments,
    required this.links,
    required this.openedAt,
    this.body,
  });

  final String id;
  final String title;
  final String? summary;
  final String languageCode;
  final bool mandatoryAcknowledgement;
  final String status;
  final DateTime? acknowledgedAt;
  final List<String> attachmentDocumentIds;
  final List<NoticeAttachmentItem> attachments;
  final List<NoticeLinkItem> links;
  final DateTime? openedAt;
  final String? body;

  factory NoticeItem.fromJson(Map<String, dynamic> json) {
    return NoticeItem(
      id: json['id'] as String,
      title: json['title'] as String,
      summary: json['summary'] as String?,
      languageCode: json['language_code'] as String,
      mandatoryAcknowledgement: json['mandatory_acknowledgement'] as bool? ?? false,
      status: json['status'] as String? ?? 'published',
      acknowledgedAt: json['acknowledged_at'] != null ? DateTime.parse(json['acknowledged_at'] as String) : null,
      openedAt: json['opened_at'] != null ? DateTime.parse(json['opened_at'] as String) : null,
      attachmentDocumentIds: (json['attachment_document_ids'] as List? ?? const []).cast<String>(),
      attachments: (json['attachments'] as List? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(NoticeAttachmentItem.fromJson)
          .toList(),
      links: (json['links'] as List? ?? const []).cast<Map<String, dynamic>>().map(NoticeLinkItem.fromJson).toList(),
      body: json['body'] as String?,
    );
  }
}

class NoticeAttachmentItem {
  const NoticeAttachmentItem({
    required this.documentId,
    required this.title,
    required this.fileName,
    required this.contentType,
    required this.currentVersionNo,
  });

  final String documentId;
  final String title;
  final String? fileName;
  final String? contentType;
  final int? currentVersionNo;

  factory NoticeAttachmentItem.fromJson(Map<String, dynamic> json) {
    return NoticeAttachmentItem(
      documentId: json['document_id'] as String,
      title: json['title'] as String,
      fileName: json['file_name'] as String?,
      contentType: json['content_type'] as String?,
      currentVersionNo: json['current_version_no'] as int?,
    );
  }
}

class NoticeLinkItem {
  const NoticeLinkItem({
    required this.id,
    required this.label,
    required this.url,
    required this.linkType,
  });

  final String id;
  final String label;
  final String url;
  final String linkType;

  factory NoticeLinkItem.fromJson(Map<String, dynamic> json) {
    return NoticeLinkItem(
      id: json['id'] as String,
      label: json['label'] as String,
      url: json['url'] as String,
      linkType: json['link_type'] as String? ?? 'external',
    );
  }
}

class NoticeFeedStatus {
  const NoticeFeedStatus({
    required this.totalCount,
    required this.unreadCount,
    required this.mandatoryUnacknowledgedCount,
    required this.blockingRequired,
  });

  final int totalCount;
  final int unreadCount;
  final int mandatoryUnacknowledgedCount;
  final bool blockingRequired;

  factory NoticeFeedStatus.fromJson(Map<String, dynamic> json) {
    return NoticeFeedStatus(
      totalCount: json['total_count'] as int? ?? 0,
      unreadCount: json['unread_count'] as int? ?? 0,
      mandatoryUnacknowledgedCount: json['mandatory_unacknowledged_count'] as int? ?? 0,
      blockingRequired: json['blocking_required'] as bool? ?? false,
    );
  }
}

class WatchbookListItem {
  const WatchbookListItem({
    required this.id,
    required this.contextType,
    required this.logDate,
    required this.headline,
    required this.reviewStatusCode,
    required this.closureStateCode,
  });

  final String id;
  final String contextType;
  final DateTime logDate;
  final String? headline;
  final String reviewStatusCode;
  final String closureStateCode;

  factory WatchbookListItem.fromJson(Map<String, dynamic> json) {
    return WatchbookListItem(
      id: json['id'] as String,
      contextType: json['context_type'] as String,
      logDate: DateTime.parse(json['log_date'] as String),
      headline: json['headline'] as String?,
      reviewStatusCode: json['review_status_code'] as String? ?? 'pending',
      closureStateCode: json['closure_state_code'] as String? ?? 'open',
    );
  }
}

class WatchbookEntryItem {
  const WatchbookEntryItem({
    required this.id,
    required this.watchbookId,
    required this.occurredAt,
    required this.entryTypeCode,
    required this.narrative,
    required this.authorActorType,
  });

  final String id;
  final String watchbookId;
  final DateTime occurredAt;
  final String entryTypeCode;
  final String narrative;
  final String authorActorType;

  factory WatchbookEntryItem.fromJson(Map<String, dynamic> json) {
    return WatchbookEntryItem(
      id: json['id'] as String,
      watchbookId: json['watchbook_id'] as String,
      occurredAt: DateTime.parse(json['occurred_at'] as String),
      entryTypeCode: json['entry_type_code'] as String,
      narrative: json['narrative'] as String,
      authorActorType: json['author_actor_type'] as String? ?? 'internal',
    );
  }
}

class WatchbookReadModel {
  const WatchbookReadModel({
    required this.id,
    required this.contextType,
    required this.logDate,
    required this.headline,
    required this.summary,
    required this.reviewStatusCode,
    required this.closureStateCode,
    required this.entries,
  });

  final String id;
  final String contextType;
  final DateTime logDate;
  final String? headline;
  final String? summary;
  final String reviewStatusCode;
  final String closureStateCode;
  final List<WatchbookEntryItem> entries;

  factory WatchbookReadModel.fromJson(Map<String, dynamic> json) {
    return WatchbookReadModel(
      id: json['id'] as String,
      contextType: json['context_type'] as String,
      logDate: DateTime.parse(json['log_date'] as String),
      headline: json['headline'] as String?,
      summary: json['summary'] as String?,
      reviewStatusCode: json['review_status_code'] as String? ?? 'pending',
      closureStateCode: json['closure_state_code'] as String? ?? 'open',
      entries: (json['entries'] as List? ?? const []).cast<Map<String, dynamic>>().map(WatchbookEntryItem.fromJson).toList(),
    );
  }
}

class PatrolCheckpointProgressItem {
  const PatrolCheckpointProgressItem({
    required this.checkpointId,
    required this.sequenceNo,
    required this.checkpointCode,
    required this.label,
    required this.scanTypeCode,
    required this.minimumDwellSeconds,
    required this.isCompleted,
    required this.lastEventAt,
  });

  final String checkpointId;
  final int sequenceNo;
  final String checkpointCode;
  final String label;
  final String scanTypeCode;
  final int minimumDwellSeconds;
  final bool isCompleted;
  final DateTime? lastEventAt;

  factory PatrolCheckpointProgressItem.fromJson(Map<String, dynamic> json) {
    return PatrolCheckpointProgressItem(
      checkpointId: json['checkpoint_id'] as String,
      sequenceNo: json['sequence_no'] as int,
      checkpointCode: json['checkpoint_code'] as String,
      label: json['label'] as String,
      scanTypeCode: json['scan_type_code'] as String,
      minimumDwellSeconds: json['minimum_dwell_seconds'] as int? ?? 0,
      isCompleted: json['is_completed'] as bool? ?? false,
      lastEventAt: json['last_event_at'] != null ? DateTime.parse(json['last_event_at'] as String) : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'checkpoint_id': checkpointId,
    'sequence_no': sequenceNo,
    'checkpoint_code': checkpointCode,
    'label': label,
    'scan_type_code': scanTypeCode,
    'minimum_dwell_seconds': minimumDwellSeconds,
    'is_completed': isCompleted,
    'last_event_at': lastEventAt?.toIso8601String(),
  };
}

class PatrolAvailableRouteItem {
  const PatrolAvailableRouteItem({
    required this.shiftId,
    required this.planningRecordId,
    required this.patrolRouteId,
    required this.routeNo,
    required this.routeName,
    required this.scheduleDate,
    required this.workStart,
    required this.workEnd,
    required this.meetingPoint,
    required this.locationLabel,
    required this.checkpointCount,
    required this.checkpoints,
  });

  final String shiftId;
  final String? planningRecordId;
  final String patrolRouteId;
  final String routeNo;
  final String routeName;
  final DateTime scheduleDate;
  final DateTime workStart;
  final DateTime workEnd;
  final String? meetingPoint;
  final String? locationLabel;
  final int checkpointCount;
  final List<PatrolCheckpointProgressItem> checkpoints;

  factory PatrolAvailableRouteItem.fromJson(Map<String, dynamic> json) {
    return PatrolAvailableRouteItem(
      shiftId: json['shift_id'] as String,
      planningRecordId: json['planning_record_id'] as String?,
      patrolRouteId: json['patrol_route_id'] as String,
      routeNo: json['route_no'] as String,
      routeName: json['route_name'] as String,
      scheduleDate: DateTime.parse(json['schedule_date'] as String),
      workStart: DateTime.parse(json['work_start'] as String),
      workEnd: DateTime.parse(json['work_end'] as String),
      meetingPoint: json['meeting_point'] as String?,
      locationLabel: json['location_label'] as String?,
      checkpointCount: json['checkpoint_count'] as int? ?? 0,
      checkpoints: (json['checkpoints'] as List? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(PatrolCheckpointProgressItem.fromJson)
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'shift_id': shiftId,
    'planning_record_id': planningRecordId,
    'patrol_route_id': patrolRouteId,
    'route_no': routeNo,
    'route_name': routeName,
    'schedule_date': scheduleDate.toIso8601String(),
    'work_start': workStart.toIso8601String(),
    'work_end': workEnd.toIso8601String(),
    'meeting_point': meetingPoint,
    'location_label': locationLabel,
    'checkpoint_count': checkpointCount,
    'checkpoints': checkpoints.map((item) => item.toJson()).toList(),
  };
}

class PatrolRoundEventItem {
  const PatrolRoundEventItem({
    required this.id,
    required this.patrolRoundId,
    required this.sequenceNo,
    required this.checkpointId,
    required this.occurredAt,
    required this.eventTypeCode,
    required this.scanMethodCode,
    required this.tokenValue,
    required this.note,
    required this.reasonCode,
    required this.actorUserId,
    required this.isPolicyCompliant,
    required this.clientEventId,
    required this.attachmentDocumentIds,
  });

  final String id;
  final String patrolRoundId;
  final int sequenceNo;
  final String? checkpointId;
  final DateTime occurredAt;
  final String eventTypeCode;
  final String? scanMethodCode;
  final String? tokenValue;
  final String? note;
  final String? reasonCode;
  final String actorUserId;
  final bool isPolicyCompliant;
  final String? clientEventId;
  final List<String> attachmentDocumentIds;

  factory PatrolRoundEventItem.fromJson(Map<String, dynamic> json) {
    return PatrolRoundEventItem(
      id: json['id'] as String,
      patrolRoundId: json['patrol_round_id'] as String,
      sequenceNo: json['sequence_no'] as int,
      checkpointId: json['checkpoint_id'] as String?,
      occurredAt: DateTime.parse(json['occurred_at'] as String),
      eventTypeCode: json['event_type_code'] as String,
      scanMethodCode: json['scan_method_code'] as String?,
      tokenValue: json['token_value'] as String?,
      note: json['note'] as String?,
      reasonCode: json['reason_code'] as String?,
      actorUserId: json['actor_user_id'] as String,
      isPolicyCompliant: json['is_policy_compliant'] as bool? ?? false,
      clientEventId: json['client_event_id'] as String?,
      attachmentDocumentIds: (json['attachment_document_ids'] as List? ?? const []).cast<String>(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'patrol_round_id': patrolRoundId,
    'sequence_no': sequenceNo,
    'checkpoint_id': checkpointId,
    'occurred_at': occurredAt.toIso8601String(),
    'event_type_code': eventTypeCode,
    'scan_method_code': scanMethodCode,
    'token_value': tokenValue,
    'note': note,
    'reason_code': reasonCode,
    'actor_user_id': actorUserId,
    'is_policy_compliant': isPolicyCompliant,
    'client_event_id': clientEventId,
    'attachment_document_ids': attachmentDocumentIds,
  };
}

class PatrolRoundItem {
  const PatrolRoundItem({
    required this.id,
    required this.tenantId,
    required this.employeeId,
    required this.shiftId,
    required this.planningRecordId,
    required this.patrolRouteId,
    required this.watchbookId,
    required this.summaryDocumentId,
    required this.offlineSyncToken,
    required this.roundStatusCode,
    required this.startedAt,
    required this.completedAt,
    required this.abortedAt,
    required this.abortReasonCode,
    required this.completionNote,
    required this.totalCheckpointCount,
    required this.completedCheckpointCount,
    required this.versionNo,
    required this.events,
    required this.checkpoints,
  });

  final String id;
  final String tenantId;
  final String employeeId;
  final String shiftId;
  final String? planningRecordId;
  final String patrolRouteId;
  final String? watchbookId;
  final String? summaryDocumentId;
  final String? offlineSyncToken;
  final String roundStatusCode;
  final DateTime startedAt;
  final DateTime? completedAt;
  final DateTime? abortedAt;
  final String? abortReasonCode;
  final String? completionNote;
  final int totalCheckpointCount;
  final int completedCheckpointCount;
  final int versionNo;
  final List<PatrolRoundEventItem> events;
  final List<PatrolCheckpointProgressItem> checkpoints;

  factory PatrolRoundItem.fromJson(Map<String, dynamic> json) {
    return PatrolRoundItem(
      id: json['id'] as String,
      tenantId: json['tenant_id'] as String,
      employeeId: json['employee_id'] as String,
      shiftId: json['shift_id'] as String,
      planningRecordId: json['planning_record_id'] as String?,
      patrolRouteId: json['patrol_route_id'] as String,
      watchbookId: json['watchbook_id'] as String?,
      summaryDocumentId: json['summary_document_id'] as String?,
      offlineSyncToken: json['offline_sync_token'] as String?,
      roundStatusCode: json['round_status_code'] as String,
      startedAt: DateTime.parse(json['started_at'] as String),
      completedAt: json['completed_at'] != null ? DateTime.parse(json['completed_at'] as String) : null,
      abortedAt: json['aborted_at'] != null ? DateTime.parse(json['aborted_at'] as String) : null,
      abortReasonCode: json['abort_reason_code'] as String?,
      completionNote: json['completion_note'] as String?,
      totalCheckpointCount: json['total_checkpoint_count'] as int? ?? 0,
      completedCheckpointCount: json['completed_checkpoint_count'] as int? ?? 0,
      versionNo: json['version_no'] as int? ?? 1,
      events: (json['events'] as List? ?? const []).cast<Map<String, dynamic>>().map(PatrolRoundEventItem.fromJson).toList(),
      checkpoints: (json['checkpoints'] as List? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(PatrolCheckpointProgressItem.fromJson)
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'tenant_id': tenantId,
    'employee_id': employeeId,
    'shift_id': shiftId,
    'planning_record_id': planningRecordId,
    'patrol_route_id': patrolRouteId,
    'watchbook_id': watchbookId,
    'summary_document_id': summaryDocumentId,
    'offline_sync_token': offlineSyncToken,
    'round_status_code': roundStatusCode,
    'started_at': startedAt.toIso8601String(),
    'completed_at': completedAt?.toIso8601String(),
    'aborted_at': abortedAt?.toIso8601String(),
    'abort_reason_code': abortReasonCode,
    'completion_note': completionNote,
    'total_checkpoint_count': totalCheckpointCount,
    'completed_checkpoint_count': completedCheckpointCount,
    'version_no': versionNo,
    'events': events.map((item) => item.toJson()).toList(),
    'checkpoints': checkpoints.map((item) => item.toJson()).toList(),
  };
}

class PatrolEvidenceAttachmentPayload {
  const PatrolEvidenceAttachmentPayload({
    required this.fileName,
    required this.contentType,
    required this.contentBase64,
    this.title,
  });

  final String fileName;
  final String contentType;
  final String contentBase64;
  final String? title;

  Map<String, dynamic> toJson() => {
    'title': title,
    'file_name': fileName,
    'content_type': contentType,
    'content_base64': contentBase64,
  };
}

class PatrolRoundStartPayload {
  const PatrolRoundStartPayload({
    required this.shiftId,
    required this.patrolRouteId,
    required this.offlineSyncToken,
  });

  final String shiftId;
  final String patrolRouteId;
  final String offlineSyncToken;

  Map<String, dynamic> toJson() => {
    'shift_id': shiftId,
    'patrol_route_id': patrolRouteId,
    'offline_sync_token': offlineSyncToken,
  };
}

class PatrolRoundCapturePayload {
  const PatrolRoundCapturePayload({
    required this.scanMethodCode,
    required this.clientEventId,
    this.checkpointId,
    this.tokenValue,
    this.latitude,
    this.longitude,
    this.note,
    this.reasonCode,
    this.occurredAt,
    this.offlineSequenceNo,
    this.attachments = const [],
  });

  final String scanMethodCode;
  final String clientEventId;
  final String? checkpointId;
  final String? tokenValue;
  final double? latitude;
  final double? longitude;
  final String? note;
  final String? reasonCode;
  final DateTime? occurredAt;
  final int? offlineSequenceNo;
  final List<PatrolEvidenceAttachmentPayload> attachments;

  Map<String, dynamic> toJson() => {
    'checkpoint_id': checkpointId,
    'scan_method_code': scanMethodCode,
    'token_value': tokenValue,
    'latitude': latitude,
    'longitude': longitude,
    'note': note,
    'reason_code': reasonCode,
    'occurred_at': occurredAt?.toIso8601String(),
    'offline_sequence_no': offlineSequenceNo,
    'client_event_id': clientEventId,
    'attachments': attachments.map((item) => item.toJson()).toList(),
  };
}

class PatrolRoundCompletePayload {
  const PatrolRoundCompletePayload({
    required this.clientEventId,
    this.note,
    this.occurredAt,
    this.offlineSequenceNo,
  });

  final String clientEventId;
  final String? note;
  final DateTime? occurredAt;
  final int? offlineSequenceNo;

  Map<String, dynamic> toJson() => {
    'note': note,
    'occurred_at': occurredAt?.toIso8601String(),
    'offline_sequence_no': offlineSequenceNo,
    'client_event_id': clientEventId,
  };
}

class PatrolRoundAbortPayload {
  const PatrolRoundAbortPayload({
    required this.abortReasonCode,
    required this.clientEventId,
    this.note,
    this.occurredAt,
    this.offlineSequenceNo,
    this.attachments = const [],
  });

  final String abortReasonCode;
  final String clientEventId;
  final String? note;
  final DateTime? occurredAt;
  final int? offlineSequenceNo;
  final List<PatrolEvidenceAttachmentPayload> attachments;

  Map<String, dynamic> toJson() => {
    'abort_reason_code': abortReasonCode,
    'note': note,
    'occurred_at': occurredAt?.toIso8601String(),
    'offline_sequence_no': offlineSequenceNo,
    'client_event_id': clientEventId,
    'attachments': attachments.map((item) => item.toJson()).toList(),
  };
}

class PatrolEvaluationItem {
  const PatrolEvaluationItem({
    required this.patrolRoundId,
    required this.tenantId,
    required this.employeeId,
    required this.patrolRouteId,
    required this.roundStatusCode,
    required this.totalCheckpointCount,
    required this.completedCheckpointCount,
    required this.exceptionCount,
    required this.manualCaptureCount,
    required this.mismatchCount,
    required this.watchbookId,
    required this.summaryDocument,
    required this.completionRatio,
    required this.complianceStatusCode,
  });

  final String patrolRoundId;
  final String tenantId;
  final String employeeId;
  final String patrolRouteId;
  final String roundStatusCode;
  final int totalCheckpointCount;
  final int completedCheckpointCount;
  final int exceptionCount;
  final int manualCaptureCount;
  final int mismatchCount;
  final String? watchbookId;
  final EmployeeReleasedDocument? summaryDocument;
  final double completionRatio;
  final String complianceStatusCode;

  factory PatrolEvaluationItem.fromJson(Map<String, dynamic> json) {
    return PatrolEvaluationItem(
      patrolRoundId: json['patrol_round_id'] as String,
      tenantId: json['tenant_id'] as String,
      employeeId: json['employee_id'] as String,
      patrolRouteId: json['patrol_route_id'] as String,
      roundStatusCode: json['round_status_code'] as String,
      totalCheckpointCount: json['total_checkpoint_count'] as int? ?? 0,
      completedCheckpointCount: json['completed_checkpoint_count'] as int? ?? 0,
      exceptionCount: json['exception_count'] as int? ?? 0,
      manualCaptureCount: json['manual_capture_count'] as int? ?? 0,
      mismatchCount: json['mismatch_count'] as int? ?? 0,
      watchbookId: json['watchbook_id'] as String?,
      summaryDocument: json['summary_document'] != null
          ? EmployeeReleasedDocument.fromJson((json['summary_document'] as Map).cast<String, dynamic>())
          : null,
      completionRatio: (json['completion_ratio'] as num?)?.toDouble() ?? 0,
      complianceStatusCode: json['compliance_status_code'] as String? ?? 'attention_required',
    );
  }
}

abstract class MobileBackendGateway {
  Future<(MobileCurrentUser, MobileAuthTokens)> login(MobileLoginPayload payload);
  Future<(MobileCurrentUser, MobileAuthTokens)> restore(MobileAuthTokens tokens);
  Future<EmployeeMobileContext> fetchMobileContext(String accessToken);
  Future<List<EmployeeReleasedScheduleItem>> fetchReleasedSchedules(String accessToken);
  Future<List<TimeCaptureEventItem>> fetchTimeEvents(String accessToken);
  Future<TimeCaptureEventItem> captureOwnTimeEvent(
    String accessToken, {
    required String sourceChannelCode,
    required TimeCapturePayload payload,
  });
  Future<EmployeeReleasedScheduleItem> respondToAssignment(
    String accessToken, {
    required String assignmentId,
    required String responseCode,
    required int? versionNo,
    String? note,
  });
  Future<List<EmployeeEventApplicationItem>> fetchEventApplications(String accessToken);
  Future<EmployeeEventApplicationItem> createEventApplication(
    String accessToken, {
    required String planningRecordId,
    String? note,
  });
  Future<EmployeeEventApplicationItem> cancelEventApplication(
    String accessToken, {
    required String applicationId,
    required int? versionNo,
    String? decisionNote,
  });
  Future<List<EmployeeMobileDocument>> fetchDocuments(String accessToken);
  Future<List<EmployeeMobileCredential>> fetchCredentials(String accessToken);
  Future<List<NoticeItem>> fetchNotices(String accessToken, String tenantId);
  Future<NoticeFeedStatus> fetchNoticeFeedStatus(String accessToken, String tenantId);
  Future<NoticeItem> fetchNotice(String accessToken, String tenantId, String noticeId);
  Future<void> openNotice(String accessToken, String tenantId, String noticeId);
  Future<void> acknowledgeNotice(String accessToken, String tenantId, String noticeId, {String? acknowledgementText});
  Future<List<int>> downloadNoticeAttachment(
    String accessToken, {
    required String tenantId,
    required String documentId,
    required int versionNo,
  });
  Future<List<int>> downloadOwnDocument(
    String accessToken, {
    required String documentId,
    required int versionNo,
  });
  Future<List<WatchbookListItem>> fetchWatchbooks(String accessToken, String tenantId);
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
  });
  Future<WatchbookReadModel> fetchWatchbook(String accessToken, {required String tenantId, required String watchbookId});
  Future<WatchbookEntryItem> createWatchbookEntry(
    String accessToken, {
    required String tenantId,
    required String watchbookId,
    required String entryTypeCode,
    required String narrative,
    String? trafficLightCode,
  });
  Future<List<PatrolAvailableRouteItem>> fetchPatrolRoutes(String accessToken);
  Future<PatrolRoundItem?> fetchActivePatrolRound(String accessToken);
  Future<PatrolRoundItem> startPatrolRound(String accessToken, PatrolRoundStartPayload payload);
  Future<PatrolRoundItem> fetchPatrolRound(String accessToken, String patrolRoundId);
  Future<PatrolRoundItem> capturePatrolCheckpoint(String accessToken, String patrolRoundId, PatrolRoundCapturePayload payload);
  Future<PatrolRoundItem> completePatrolRound(String accessToken, String patrolRoundId, PatrolRoundCompletePayload payload);
  Future<PatrolRoundItem> abortPatrolRound(String accessToken, String patrolRoundId, PatrolRoundAbortPayload payload);
  Future<PatrolEvaluationItem> fetchPatrolEvaluation(String accessToken, String patrolRoundId);
}

class HttpMobileBackendGateway implements MobileBackendGateway {
  HttpMobileBackendGateway({required this.config});

  final AppConfig config;

  Uri _uri(String path) => Uri.parse('${config.apiBaseUrl}$path');

  Future<Map<String, dynamic>> _jsonRequest(
    String method,
    Uri uri, {
    Map<String, dynamic>? body,
    String? accessToken,
  }) async {
    final client = HttpClient();
    try {
      final request = await client.openUrl(method, uri);
      request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');
      if (accessToken != null) {
        request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $accessToken');
      }
      if (body != null) {
        request.add(utf8.encode(jsonEncode(body)));
      }
      final response = await request.close();
      final responseBody = await response.transform(utf8.decoder).join();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final decoded = responseBody.isNotEmpty ? jsonDecode(responseBody) as Map<String, dynamic> : <String, dynamic>{};
        final errors = decoded['errors'];
        String messageKey = 'errors.platform.internal';
        if (errors is List && errors.isNotEmpty) {
          final item = (errors.first as Map).cast<String, dynamic>();
          messageKey = item['message_key'] as String? ?? messageKey;
        }
        throw MobileApiException(statusCode: response.statusCode, messageKey: messageKey, body: decoded);
      }
      if (responseBody.isEmpty) {
        return <String, dynamic>{};
      }
      return (jsonDecode(responseBody) as Map).cast<String, dynamic>();
    } finally {
      client.close(force: true);
    }
  }

  Future<List<dynamic>> _jsonList(String method, Uri uri, {String? accessToken}) async {
    final client = HttpClient();
    try {
      final request = await client.openUrl(method, uri);
      request.headers.set(HttpHeaders.contentTypeHeader, 'application/json');
      if (accessToken != null) {
        request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $accessToken');
      }
      final response = await request.close();
      final responseBody = await response.transform(utf8.decoder).join();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final decoded = responseBody.isNotEmpty ? jsonDecode(responseBody) as Map<String, dynamic> : <String, dynamic>{};
        final errors = decoded['errors'];
        String messageKey = 'errors.platform.internal';
        if (errors is List && errors.isNotEmpty) {
          final item = (errors.first as Map).cast<String, dynamic>();
          messageKey = item['message_key'] as String? ?? messageKey;
        }
        throw MobileApiException(statusCode: response.statusCode, messageKey: messageKey, body: decoded);
      }
      return responseBody.isEmpty ? const [] : jsonDecode(responseBody) as List<dynamic>;
    } finally {
      client.close(force: true);
    }
  }

  @override
  Future<(MobileCurrentUser, MobileAuthTokens)> login(MobileLoginPayload payload) async {
    final loginJson = await _jsonRequest(
      'POST',
      _uri('/api/auth/login'),
      body: {
        'tenant_code': payload.tenantCode,
        'identifier': payload.identifier,
        'password': payload.password,
        'device_label': payload.deviceLabel,
        'device_id': payload.deviceId,
      },
    );
    final tokens = MobileAuthTokens.fromLogin(loginJson);
    final codesJson = await _jsonRequest('GET', _uri('/api/auth/codes'), accessToken: tokens.accessToken);
    final user = MobileCurrentUser.fromAuthResponses(loginJson, codesJson);
    return (user, tokens);
  }

  @override
  Future<(MobileCurrentUser, MobileAuthTokens)> restore(MobileAuthTokens tokens) async {
    try {
      final meJson = await _jsonRequest('GET', _uri('/api/auth/me'), accessToken: tokens.accessToken);
      final codesJson = await _jsonRequest('GET', _uri('/api/auth/codes'), accessToken: tokens.accessToken);
      final merged = {
        'user': meJson['user'],
        'session': {'access_token': tokens.accessToken, 'refresh_token': tokens.refreshToken, 'session_id': tokens.sessionId},
      };
      return (MobileCurrentUser.fromAuthResponses(merged, codesJson), tokens);
    } on MobileApiException catch (error) {
      if (error.statusCode != 401) {
        rethrow;
      }
      final refreshJson = await _jsonRequest(
        'POST',
        _uri('/api/auth/refresh'),
        body: {'refresh_token': tokens.refreshToken},
      );
      final refreshedTokens = MobileAuthTokens(
        accessToken: (refreshJson['session'] as Map)['access_token'] as String,
        refreshToken: (refreshJson['session'] as Map)['refresh_token'] as String,
        sessionId: (refreshJson['session'] as Map)['session_id'] as String,
      );
      final meJson = await _jsonRequest('GET', _uri('/api/auth/me'), accessToken: refreshedTokens.accessToken);
      final codesJson = await _jsonRequest('GET', _uri('/api/auth/codes'), accessToken: refreshedTokens.accessToken);
      final merged = {
        'user': meJson['user'],
        'session': {
          'access_token': refreshedTokens.accessToken,
          'refresh_token': refreshedTokens.refreshToken,
          'session_id': refreshedTokens.sessionId,
        },
      };
      return (MobileCurrentUser.fromAuthResponses(merged, codesJson), refreshedTokens);
    }
  }

  @override
  Future<EmployeeMobileContext> fetchMobileContext(String accessToken) async {
    final json = await _jsonRequest('GET', _uri('/api/employee-self-service/me/mobile-context'), accessToken: accessToken);
    return EmployeeMobileContext.fromJson(json);
  }

  @override
  Future<List<EmployeeReleasedScheduleItem>> fetchReleasedSchedules(String accessToken) async {
    final json = await _jsonRequest('GET', _uri('/api/employee-self-service/me/released-schedules'), accessToken: accessToken);
    final items = (json['items'] as List? ?? const []).cast<Map<String, dynamic>>();
    return items.map(EmployeeReleasedScheduleItem.fromJson).toList();
  }

  @override
  Future<List<TimeCaptureEventItem>> fetchTimeEvents(String accessToken) async {
    final json = await _jsonRequest('GET', _uri('/api/field/time-capture/me/events'), accessToken: accessToken);
    final items = (json['items'] as List? ?? const []).cast<Map<String, dynamic>>();
    return items.map(TimeCaptureEventItem.fromJson).toList();
  }

  @override
  Future<TimeCaptureEventItem> captureOwnTimeEvent(
    String accessToken, {
    required String sourceChannelCode,
    required TimeCapturePayload payload,
  }) async {
    final json = await _jsonRequest(
      'POST',
      _uri('/api/field/time-capture/me/events/$sourceChannelCode'),
      accessToken: accessToken,
      body: payload.toJson(),
    );
    return TimeCaptureEventItem.fromJson(json);
  }

  @override
  Future<EmployeeReleasedScheduleItem> respondToAssignment(
    String accessToken, {
    required String assignmentId,
    required String responseCode,
    required int? versionNo,
    String? note,
  }) async {
    final json = await _jsonRequest(
      'POST',
      _uri('/api/employee-self-service/me/released-schedules/$assignmentId/respond'),
      accessToken: accessToken,
      body: {
        'response_code': responseCode,
        'note': note,
        'version_no': versionNo,
      },
    );
    return EmployeeReleasedScheduleItem.fromJson(json);
  }

  @override
  Future<List<EmployeeEventApplicationItem>> fetchEventApplications(String accessToken) async {
    final items = await _jsonList('GET', _uri('/api/employee-self-service/me/event-applications'), accessToken: accessToken);
    return items.cast<Map<String, dynamic>>().map(EmployeeEventApplicationItem.fromJson).toList();
  }

  @override
  Future<EmployeeEventApplicationItem> createEventApplication(
    String accessToken, {
    required String planningRecordId,
    String? note,
  }) async {
    final json = await _jsonRequest(
      'POST',
      _uri('/api/employee-self-service/me/event-applications'),
      accessToken: accessToken,
      body: {'planning_record_id': planningRecordId, 'note': note},
    );
    return EmployeeEventApplicationItem.fromJson(json);
  }

  @override
  Future<EmployeeEventApplicationItem> cancelEventApplication(
    String accessToken, {
    required String applicationId,
    required int? versionNo,
    String? decisionNote,
  }) async {
    final json = await _jsonRequest(
      'POST',
      _uri('/api/employee-self-service/me/event-applications/$applicationId/cancel'),
      accessToken: accessToken,
      body: {'decision_note': decisionNote, 'version_no': versionNo},
    );
    return EmployeeEventApplicationItem.fromJson(json);
  }

  @override
  Future<List<EmployeeMobileDocument>> fetchDocuments(String accessToken) async {
    final json = await _jsonRequest('GET', _uri('/api/employee-self-service/me/documents'), accessToken: accessToken);
    final items = (json['items'] as List? ?? const []).cast<Map<String, dynamic>>();
    return items.map(EmployeeMobileDocument.fromJson).toList();
  }

  @override
  Future<List<EmployeeMobileCredential>> fetchCredentials(String accessToken) async {
    final json = await _jsonRequest('GET', _uri('/api/employee-self-service/me/credentials'), accessToken: accessToken);
    final items = (json['items'] as List? ?? const []).cast<Map<String, dynamic>>();
    return items.map(EmployeeMobileCredential.fromJson).toList();
  }

  @override
  Future<List<NoticeItem>> fetchNotices(String accessToken, String tenantId) async {
    final items = await _jsonList(
      'GET',
      _uri('/api/platform/tenants/$tenantId/info/notices/my/feed'),
      accessToken: accessToken,
    );
    return items.cast<Map<String, dynamic>>().map(NoticeItem.fromJson).toList();
  }

  @override
  Future<NoticeFeedStatus> fetchNoticeFeedStatus(String accessToken, String tenantId) async {
    final json = await _jsonRequest('GET', _uri('/api/platform/tenants/$tenantId/info/notices/my/feed/status'), accessToken: accessToken);
    return NoticeFeedStatus.fromJson(json);
  }

  @override
  Future<NoticeItem> fetchNotice(String accessToken, String tenantId, String noticeId) async {
    final json = await _jsonRequest('GET', _uri('/api/platform/tenants/$tenantId/info/notices/my/feed/$noticeId'), accessToken: accessToken);
    return NoticeItem.fromJson(json);
  }

  @override
  Future<void> openNotice(String accessToken, String tenantId, String noticeId) async {
    await _jsonRequest('POST', _uri('/api/platform/tenants/$tenantId/info/notices/$noticeId/open'), accessToken: accessToken, body: const {});
  }

  @override
  Future<void> acknowledgeNotice(String accessToken, String tenantId, String noticeId, {String? acknowledgementText}) async {
    await _jsonRequest(
      'POST',
      _uri('/api/platform/tenants/$tenantId/info/notices/$noticeId/acknowledge'),
      accessToken: accessToken,
      body: {'acknowledgement_text': acknowledgementText},
    );
  }

  @override
  Future<List<int>> downloadNoticeAttachment(
    String accessToken, {
    required String tenantId,
    required String documentId,
    required int versionNo,
  }) async {
    final client = HttpClient();
    try {
      final request = await client.getUrl(_uri('/api/platform/tenants/$tenantId/documents/$documentId/versions/$versionNo/download'));
      request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $accessToken');
      final response = await request.close();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final responseBody = await response.transform(utf8.decoder).join();
        final decoded = responseBody.isNotEmpty ? jsonDecode(responseBody) as Map<String, dynamic> : <String, dynamic>{};
        throw MobileApiException(statusCode: response.statusCode, messageKey: 'errors.platform.internal', body: decoded);
      }
      return response.fold<List<int>>(<int>[], (buffer, chunk) {
        buffer.addAll(chunk);
        return buffer;
      });
    } finally {
      client.close(force: true);
    }
  }

  @override
  Future<List<int>> downloadOwnDocument(
    String accessToken, {
    required String documentId,
    required int versionNo,
  }) async {
    final client = HttpClient();
    try {
      final request = await client.getUrl(_uri('/api/employee-self-service/me/documents/$documentId/versions/$versionNo/download'));
      request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $accessToken');
      final response = await request.close();
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final responseBody = await response.transform(utf8.decoder).join();
        final decoded = responseBody.isNotEmpty ? jsonDecode(responseBody) as Map<String, dynamic> : <String, dynamic>{};
        throw MobileApiException(statusCode: response.statusCode, messageKey: 'errors.platform.internal', body: decoded);
      }
      return response.fold<List<int>>(<int>[], (buffer, chunk) {
        buffer.addAll(chunk);
        return buffer;
      });
    } finally {
      client.close(force: true);
    }
  }

  @override
  Future<List<WatchbookListItem>> fetchWatchbooks(String accessToken, String tenantId) async {
    final items = await _jsonList('GET', _uri('/api/field/tenants/$tenantId/watchbooks'), accessToken: accessToken);
    return items.cast<Map<String, dynamic>>().map(WatchbookListItem.fromJson).toList();
  }

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
    final json = await _jsonRequest(
      'POST',
      _uri('/api/field/tenants/$tenantId/watchbooks/open'),
      accessToken: accessToken,
      body: {
        'tenant_id': tenantId,
        'context_type': contextType,
        'log_date': logDate.toIso8601String().split('T').first,
        'site_id': siteId,
        'order_id': orderId,
        'planning_record_id': planningRecordId,
        'shift_id': shiftId,
        'headline': headline,
      },
    );
    return WatchbookReadModel.fromJson(json);
  }

  @override
  Future<WatchbookReadModel> fetchWatchbook(String accessToken, {required String tenantId, required String watchbookId}) async {
    final json = await _jsonRequest('GET', _uri('/api/field/tenants/$tenantId/watchbooks/$watchbookId'), accessToken: accessToken);
    return WatchbookReadModel.fromJson(json);
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
    final json = await _jsonRequest(
      'POST',
      _uri('/api/field/tenants/$tenantId/watchbooks/$watchbookId/entries'),
      accessToken: accessToken,
      body: {
        'entry_type_code': entryTypeCode,
        'narrative': narrative,
        'traffic_light_code': trafficLightCode,
      },
    );
    return WatchbookEntryItem.fromJson(json);
  }

  @override
  Future<List<PatrolAvailableRouteItem>> fetchPatrolRoutes(String accessToken) async {
    final items = await _jsonList('GET', _uri('/api/field/patrol/routes'), accessToken: accessToken);
    return items.cast<Map<String, dynamic>>().map(PatrolAvailableRouteItem.fromJson).toList();
  }

  @override
  Future<PatrolRoundItem?> fetchActivePatrolRound(String accessToken) async {
    final json = await _jsonRequest('GET', _uri('/api/field/patrol/rounds/active'), accessToken: accessToken);
    if (json.isEmpty || json['id'] == null) {
      return null;
    }
    return PatrolRoundItem.fromJson(json);
  }

  @override
  Future<PatrolRoundItem> startPatrolRound(String accessToken, PatrolRoundStartPayload payload) async {
    final json = await _jsonRequest(
      'POST',
      _uri('/api/field/patrol/rounds/start'),
      accessToken: accessToken,
      body: payload.toJson(),
    );
    return PatrolRoundItem.fromJson(json);
  }

  @override
  Future<PatrolRoundItem> fetchPatrolRound(String accessToken, String patrolRoundId) async {
    final json = await _jsonRequest('GET', _uri('/api/field/patrol/rounds/$patrolRoundId'), accessToken: accessToken);
    return PatrolRoundItem.fromJson(json);
  }

  @override
  Future<PatrolRoundItem> capturePatrolCheckpoint(String accessToken, String patrolRoundId, PatrolRoundCapturePayload payload) async {
    final json = await _jsonRequest(
      'POST',
      _uri('/api/field/patrol/rounds/$patrolRoundId/capture'),
      accessToken: accessToken,
      body: payload.toJson(),
    );
    return PatrolRoundItem.fromJson(json);
  }

  @override
  Future<PatrolRoundItem> completePatrolRound(String accessToken, String patrolRoundId, PatrolRoundCompletePayload payload) async {
    final json = await _jsonRequest(
      'POST',
      _uri('/api/field/patrol/rounds/$patrolRoundId/complete'),
      accessToken: accessToken,
      body: payload.toJson(),
    );
    return PatrolRoundItem.fromJson(json);
  }

  @override
  Future<PatrolRoundItem> abortPatrolRound(String accessToken, String patrolRoundId, PatrolRoundAbortPayload payload) async {
    final json = await _jsonRequest(
      'POST',
      _uri('/api/field/patrol/rounds/$patrolRoundId/abort'),
      accessToken: accessToken,
      body: payload.toJson(),
    );
    return PatrolRoundItem.fromJson(json);
  }

  @override
  Future<PatrolEvaluationItem> fetchPatrolEvaluation(String accessToken, String patrolRoundId) async {
    final json = await _jsonRequest('GET', _uri('/api/field/patrol/rounds/$patrolRoundId/evaluation'), accessToken: accessToken);
    return PatrolEvaluationItem.fromJson(json);
  }
}
