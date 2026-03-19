import '../config/app_config.dart';
import 'mobile_role.dart';

class MobileSession {
  const MobileSession({
    required this.userName,
    required this.tenantName,
    required this.role,
    required this.offlineReady,
    required this.hasPatrolAccess,
  });

  final String userName;
  final String tenantName;
  final MobileRole role;
  final bool offlineReady;
  final bool hasPatrolAccess;

  factory MobileSession.initial(AppConfig config) {
    return MobileSession(
      userName: 'Nina Becker',
      tenantName: 'SicherPlan Nord',
      role: MobileRole.employee,
      offlineReady: config.enableOfflineCache,
      hasPatrolAccess: true,
    );
  }

  MobileSession copyWith({
    String? userName,
    String? tenantName,
    MobileRole? role,
    bool? offlineReady,
    bool? hasPatrolAccess,
  }) {
    return MobileSession(
      userName: userName ?? this.userName,
      tenantName: tenantName ?? this.tenantName,
      role: role ?? this.role,
      offlineReady: offlineReady ?? this.offlineReady,
      hasPatrolAccess: hasPatrolAccess ?? this.hasPatrolAccess,
    );
  }
}
