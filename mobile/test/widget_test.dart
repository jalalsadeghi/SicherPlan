import 'package:flutter_test/flutter_test.dart';
import 'package:sicherplan_mobile/app/sicherplan_app.dart';
import 'package:sicherplan_mobile/config/app_config.dart';

void main() {
  testWidgets('mobile shell exposes German navigation labels by default', (
    tester,
  ) async {
    await tester.pumpWidget(const SicherPlanApp(config: AppConfig.current));
    await tester.pumpAndSettle();

    expect(find.text('Start'), findsOneWidget);
    expect(find.text('Plan'), findsOneWidget);
    expect(find.text('Info'), findsOneWidget);
    expect(find.text('Zeit'), findsOneWidget);
    expect(find.text('Profil'), findsOneWidget);
  });
}
