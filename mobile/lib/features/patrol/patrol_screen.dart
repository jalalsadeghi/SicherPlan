import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../session/mobile_session.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class PatrolScreen extends StatelessWidget {
  const PatrolScreen({required this.session, super.key});

  final MobileSession session;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return ShellScaffold(
      title: l10n.patrolTitle,
      subtitle: l10n.patrolSubtitle,
      children: [
        HighlightCard(
          title: l10n.patrolAccessTitle(session.hasPatrolAccess),
          subtitle: l10n.patrolAccessSubtitle(session.hasPatrolAccess),
          icon: Icons.shield_outlined,
          badge: l10n.patrolAccessBadge(session.hasPatrolAccess),
        ),
        HighlightCard(
          title: l10n.patrolIncidentTitle,
          subtitle: l10n.patrolIncidentSubtitle,
          icon: Icons.description_outlined,
        ),
      ],
    );
  }
}
