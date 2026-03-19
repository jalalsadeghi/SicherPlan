import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../session/mobile_role.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class TimeCaptureScreen extends StatelessWidget {
  const TimeCaptureScreen({
    required this.role,
    required this.offlineReady,
    super.key,
  });

  final MobileRole role;
  final bool offlineReady;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return ShellScaffold(
      title: l10n.timeTitle,
      subtitle: l10n.timeSubtitle,
      children: [
        HighlightCard(
          title: l10n.timeStartTitle,
          subtitle: l10n.timeStartSubtitle(offlineReady),
          icon: Icons.play_circle_outline_rounded,
          badge: l10n.timeModeBadge(offlineReady),
        ),
        HighlightCard(
          title: l10n.timeApprovalTitle(role),
          subtitle: l10n.timeApprovalSubtitle(role),
          icon: Icons.badge_outlined,
        ),
      ],
    );
  }
}
