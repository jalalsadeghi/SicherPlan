import 'dart:convert';
import 'dart:io';

import '../api/mobile_backend.dart';

class StoredMobileSession {
  const StoredMobileSession({
    required this.tokens,
    required this.user,
    required this.context,
  });

  final MobileAuthTokens tokens;
  final MobileCurrentUser user;
  final EmployeeMobileContext context;

  Map<String, dynamic> toJson() => {
    'tokens': tokens.toJson(),
    'user': user.toJson(),
    'context': context.toJson(),
  };

  factory StoredMobileSession.fromJson(Map<String, dynamic> json) {
    return StoredMobileSession(
      tokens: MobileAuthTokens.fromJson(
        (json['tokens'] as Map).cast<String, dynamic>(),
      ),
      user: MobileCurrentUser.fromJson(
        (json['user'] as Map).cast<String, dynamic>(),
      ),
      context: EmployeeMobileContext.fromJson(
        (json['context'] as Map).cast<String, dynamic>(),
      ),
    );
  }
}

abstract class MobileSessionStore {
  Future<StoredMobileSession?> read();
  Future<void> write(StoredMobileSession session);
  Future<void> clear();
}

class FileMobileSessionStore implements MobileSessionStore {
  FileMobileSessionStore({String? filePath})
    : _file = File(
        filePath ??
            '${Directory.systemTemp.path}/sicherplan_mobile_session.json',
      );

  final File _file;

  @override
  Future<StoredMobileSession?> read() async {
    if (!await _file.exists()) {
      return null;
    }
    final raw = await _file.readAsString();
    if (raw.trim().isEmpty) {
      return null;
    }
    return StoredMobileSession.fromJson(
      (jsonDecode(raw) as Map).cast<String, dynamic>(),
    );
  }

  @override
  Future<void> write(StoredMobileSession session) async {
    await _file.parent.create(recursive: true);
    await _file.writeAsString(jsonEncode(session.toJson()), flush: true);
  }

  @override
  Future<void> clear() async {
    if (await _file.exists()) {
      await _file.delete();
    }
  }
}
