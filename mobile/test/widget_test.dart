import 'package:flutter_test/flutter_test.dart';
import 'package:sicherplan_mobile/app/sicherplan_app.dart';
import 'package:sicherplan_mobile/config/app_config.dart';
import 'package:sicherplan_mobile/session/mobile_session_store.dart';

class _EmptyStore implements MobileSessionStore {
  @override
  Future<void> clear() async {}

  @override
  Future<StoredMobileSession?> read() async => null;

  @override
  Future<void> write(StoredMobileSession session) async {}
}

void main() {
  testWidgets('mobile shell starts with German employee login labels', (
    tester,
  ) async {
    await tester.pumpWidget(
      SicherPlanApp(
        config: AppConfig.current,
        storeOverride: _EmptyStore(),
      ),
    );
    for (var i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }

    expect(find.text('Mitarbeiter-App'), findsOneWidget);
    expect(find.text('Mandant'), findsOneWidget);
    expect(find.text('Benutzername oder E-Mail'), findsOneWidget);
    expect(find.text('Passwort'), findsOneWidget);
    expect(find.text('Anmelden'), findsOneWidget);
  });
}
