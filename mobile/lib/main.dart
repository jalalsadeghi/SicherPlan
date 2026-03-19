import 'package:flutter/widgets.dart';

import 'app/sicherplan_app.dart';
import 'config/app_config.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(SicherPlanApp(config: AppConfig.current));
}
