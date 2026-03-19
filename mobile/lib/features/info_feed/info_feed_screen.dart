import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class InfoFeedScreen extends StatelessWidget {
  const InfoFeedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return ShellScaffold(
      title: l10n.feedTitle,
      subtitle: l10n.feedSubtitle,
      children: [
        HighlightCard(
          title: l10n.feedTrafficTitle,
          subtitle: l10n.feedTrafficSubtitle,
          icon: Icons.traffic_rounded,
          badge: l10n.newBadge,
        ),
        HighlightCard(
          title: l10n.feedUniformTitle,
          subtitle: l10n.feedUniformSubtitle,
          icon: Icons.fact_check_outlined,
        ),
      ],
    );
  }
}
