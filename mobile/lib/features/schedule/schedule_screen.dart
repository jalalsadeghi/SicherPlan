import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../session/mobile_role.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class ScheduleScreen extends StatelessWidget {
  const ScheduleScreen({required this.role, super.key});

  final MobileRole role;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return ShellScaffold(
      title: l10n.scheduleTitle,
      subtitle: l10n.scheduleSubtitle,
      children: [
        HighlightCard(
          title: l10n.scheduleCardTitle,
          subtitle: l10n.scheduleCardSubtitle,
          icon: Icons.calendar_month_rounded,
          badge: l10n.releasedBadge,
        ),
        HighlightCard(
          title: l10n.schedulePrepTitle(role),
          subtitle: l10n.schedulePrepSubtitle(role),
          icon: Icons.groups_rounded,
        ),
      ],
    );
  }
}
