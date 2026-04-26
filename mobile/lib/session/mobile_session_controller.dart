import 'dart:async';

import 'package:flutter/foundation.dart';

import '../api/mobile_backend.dart';
import 'mobile_session_store.dart';

enum MobileSessionPhase {
  bootstrapping,
  unauthenticated,
  authenticated,
  forbidden,
  blocked,
  error,
}

class MobileSessionController extends ChangeNotifier {
  MobileSessionController({
    required MobileBackendGateway backend,
    required MobileSessionStore store,
  }) : _backend = backend,
       _store = store;

  final MobileBackendGateway _backend;
  final MobileSessionStore _store;

  MobileSessionPhase _phase = MobileSessionPhase.bootstrapping;
  MobileCurrentUser? _user;
  MobileAuthTokens? _tokens;
  EmployeeMobileContext? _context;
  String? _messageKey;
  bool _busy = false;

  MobileSessionPhase get phase => _phase;
  MobileCurrentUser? get user => _user;
  MobileAuthTokens? get tokens => _tokens;
  EmployeeMobileContext? get context => _context;
  String? get messageKey => _messageKey;
  bool get busy => _busy;
  bool get isAuthenticated =>
      _phase == MobileSessionPhase.authenticated &&
      _tokens != null &&
      _context != null;

  Future<void> bootstrap() async {
    _phase = MobileSessionPhase.bootstrapping;
    _messageKey = null;
    notifyListeners();
    final stored = await _store.read();
    if (stored == null) {
      _phase = MobileSessionPhase.unauthenticated;
      notifyListeners();
      return;
    }
    try {
      final (user, tokens) = await _backend.restore(stored.tokens);
      final context = await _backend.fetchMobileContext(tokens.accessToken);
      _acceptSession(user, tokens, context);
      notifyListeners();
    } on MobileApiException catch (error) {
      await _store.clear();
      _clearState();
      _messageKey = error.messageKey;
      _phase = error.statusCode == 401
          ? MobileSessionPhase.unauthenticated
          : MobileSessionPhase.forbidden;
      notifyListeners();
    } catch (_) {
      _clearState();
      _phase = MobileSessionPhase.error;
      notifyListeners();
    }
  }

  Future<void> login({
    required String tenantCode,
    required String identifier,
    required String password,
    required String deviceLabel,
    required String deviceId,
  }) async {
    _busy = true;
    _messageKey = null;
    notifyListeners();
    try {
      final (user, tokens) = await _backend.login(
        MobileLoginPayload(
          tenantCode: tenantCode,
          identifier: identifier,
          password: password,
          deviceLabel: deviceLabel,
          deviceId: deviceId,
        ),
      );
      final context = await _backend.fetchMobileContext(tokens.accessToken);
      _acceptSession(user, tokens, context);
    } on MobileApiException catch (error) {
      await _store.clear();
      _clearState();
      _messageKey = error.messageKey;
      _phase = switch (error.statusCode) {
        401 => MobileSessionPhase.unauthenticated,
        403 => MobileSessionPhase.forbidden,
        409 => MobileSessionPhase.blocked,
        _ => MobileSessionPhase.error,
      };
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _store.clear();
    _clearState();
    _phase = MobileSessionPhase.unauthenticated;
    notifyListeners();
  }

  Future<T> withAccessToken<T>(
    Future<T> Function(String accessToken) fn,
  ) async {
    final accessToken = _tokens?.accessToken;
    if (accessToken == null) {
      throw const MobileApiException(
        statusCode: 401,
        messageKey: 'errors.iam.auth.invalid_access_token',
      );
    }
    try {
      return await fn(accessToken);
    } on MobileApiException catch (error) {
      if (error.statusCode == 401) {
        await logout();
      }
      rethrow;
    }
  }

  void _acceptSession(
    MobileCurrentUser user,
    MobileAuthTokens tokens,
    EmployeeMobileContext context,
  ) {
    final allowedRole = context.roleKeys.contains('employee_user');
    if (!allowedRole) {
      throw const MobileApiException(
        statusCode: 403,
        messageKey: 'errors.iam.authorization.permission_denied',
      );
    }
    _user = user;
    _tokens = tokens;
    _context = context;
    _phase = MobileSessionPhase.authenticated;
    unawaited(
      _store.write(
        StoredMobileSession(tokens: tokens, user: user, context: context),
      ),
    );
  }

  void _clearState() {
    _user = null;
    _tokens = null;
    _context = null;
  }
}
