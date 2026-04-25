import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sicherplan_mobile/api/mobile_backend.dart';
import 'package:sicherplan_mobile/app/sicherplan_app.dart';
import 'package:sicherplan_mobile/config/app_config.dart';
import 'package:sicherplan_mobile/session/mobile_session_store.dart';

class _MemoryStore implements MobileSessionStore {
  _MemoryStore(this.value);

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

class _FakeBackend extends Fake implements MobileBackendGateway {
  _FakeBackend({required this.context});

  final EmployeeMobileContext context;
  final List<int> photoBytes = const <int>[
    137,
    80,
    78,
    71,
    13,
    10,
    26,
    10,
    0,
    0,
    0,
    13,
    73,
    72,
    68,
    82,
    0,
    0,
    0,
    1,
    0,
    0,
    0,
    1,
    8,
    6,
    0,
    0,
    0,
    31,
    21,
    196,
    137,
    0,
    0,
    0,
    13,
    73,
    68,
    65,
    84,
    120,
    156,
    99,
    248,
    255,
    255,
    63,
    0,
    5,
    254,
    2,
    254,
    167,
    53,
    129,
    132,
    0,
    0,
    0,
    0,
    73,
    69,
    78,
    68,
    174,
    66,
    96,
    130,
  ];

  final _user = const MobileCurrentUser(
    id: 'user-1',
    tenantId: 'tenant-1',
    username: 'anna',
    fullName: 'Anna Meyer',
    locale: 'de',
    timezone: 'Europe/Berlin',
    roleKeys: ['employee_user'],
    permissionKeys: ['portal.employee.access', 'platform.info.read'],
  );

  final _tokens = const MobileAuthTokens(
    accessToken: 'access',
    refreshToken: 'refresh',
    sessionId: 'session',
  );

  @override
  Future<(MobileCurrentUser, MobileAuthTokens)> restore(
    MobileAuthTokens tokens,
  ) async => (_user, _tokens);

  @override
  Future<EmployeeMobileContext> fetchMobileContext(String accessToken) async =>
      context;

  @override
  Future<List<int>> downloadOwnDocument(
    String accessToken, {
    required String documentId,
    required int versionNo,
  }) async {
    if (documentId == 'photo-doc-1' && versionNo == 1) {
      return photoBytes;
    }
    return const <int>[];
  }
}

void main() {
  const context = EmployeeMobileContext(
    tenantId: '0af7b7f6-09c1-44eb-b58d-6acdf4f5fabc',
    tenantCode: 'nord',
    tenantName: 'SicherPlan Nord',
    photoDocumentId: 'photo-doc-1',
    photoCurrentVersionNo: 1,
    photoContentType: 'image/png',
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

  const noPhotoContext = EmployeeMobileContext(
    tenantId: '0af7b7f6-09c1-44eb-b58d-6acdf4f5fabc',
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

  Future<void> pumpHome(
    WidgetTester tester, {
    Size size = const Size(390, 844),
    EmployeeMobileContext activeContext = context,
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    final store = _MemoryStore(
      StoredMobileSession(
        tokens: const MobileAuthTokens(
          accessToken: 'seed-access',
          refreshToken: 'seed-refresh',
          sessionId: 'seed-session',
        ),
        user: const MobileCurrentUser(
          id: 'user-1',
          tenantId: 'tenant-1',
          username: 'anna',
          fullName: 'Anna Meyer',
          locale: 'de',
          timezone: 'Europe/Berlin',
          roleKeys: ['employee_user'],
          permissionKeys: ['portal.employee.access', 'platform.info.read'],
        ),
        context: activeContext,
      ),
    );

    await tester.pumpWidget(
      SicherPlanApp(
        config: const AppConfig(
          env: 'production',
          apiBaseUrl: 'https://api.example.invalid',
          defaultLocale: 'de',
          fallbackLocale: 'en',
          lightPrimary: '40,170,170',
          darkPrimary: '35,200,205',
          enableMockAuth: false,
          enableOfflineCache: true,
        ),
        backendOverride: _FakeBackend(context: activeContext),
        storeOverride: store,
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));
  }

  testWidgets('home removes the top title and subtitle above the hero card', (
    tester,
  ) async {
    await pumpHome(tester);

    expect(find.text('SicherPlan Mobil'), findsNothing);
    expect(
      find.text('Freigegebene Einsaetze, Meldungen und Selbstservice'),
      findsNothing,
    );
  });

  testWidgets(
    'home keeps the greeting and removes generic hero copy and extra identity card',
    (tester) async {
      await pumpHome(tester);

      expect(find.text('Hallo Anna'), findsOneWidget);
      expect(find.text('EMP-1 • Anna Meyer'), findsOneWidget);
      expect(
        find.text('Bereit fuer mobile Feld- und Mitarbeiterprozesse.'),
        findsNothing,
      );
      expect(find.text('Eigener Mitarbeiterkontext'), findsNothing);
      expect(find.text('SicherPlan Nord (nord)'), findsNothing);
    },
  );

  testWidgets('home still renders cleanly on a narrow mobile layout', (
    tester,
  ) async {
    await pumpHome(tester, size: const Size(360, 780));

    expect(find.text('Hallo Anna'), findsOneWidget);
    expect(find.text('EMP-1 • Anna Meyer'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'home uses the employee profile photo in the hero when available',
    (tester) async {
      await pumpHome(tester);
      await tester.pump();

      expect(find.byType(Image), findsOneWidget);
      expect(find.text('SP'), findsNothing);
    },
  );

  testWidgets('home uses initials fallback when no photo exists', (
    tester,
  ) async {
    await pumpHome(tester, activeContext: noPhotoContext);
    await tester.pump();

    expect(find.text('AM'), findsOneWidget);
    expect(find.text('SP'), findsNothing);
  });
}
