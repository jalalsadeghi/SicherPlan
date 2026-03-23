import 'package:flutter/material.dart';

import '../../config/app_config.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session_controller.dart';
import '../../widgets/brand_banner.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/shell_scaffold.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    required this.config,
    required this.controller,
    super.key,
  });

  final AppConfig config;
  final MobileSessionController controller;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final mobileContext = controller.context!;

    return ShellScaffold(
      title: l10n.homeTitle,
      subtitle: l10n.homeSubtitle,
      children: [
        BrandBanner(
          title: l10n.homeGreeting(mobileContext.preferredName ?? mobileContext.fullName),
          subtitle: l10n.homeBannerSubtitle,
          tenantName: mobileContext.tenantId,
          trailing: Icon(
            mobileContext.hasPatrolAccess ? Icons.verified_user_rounded : Icons.lock_outline_rounded,
            color: Colors.white,
          ),
        ),
        HighlightCard(
          title: l10n.mobileIdentityTitle,
          subtitle: '${mobileContext.personnelNo} • ${mobileContext.fullName}',
          icon: Icons.badge_outlined,
          badge: mobileContext.appRole,
        ),
        HighlightCard(
          title: l10n.offlineReadinessTitle,
          subtitle: l10n.offlineReadinessSubtitle(config.enableOfflineCache),
          icon: Icons.sync_rounded,
          badge: config.env,
        ),
        HighlightCard(
          title: l10n.mobileShellGuardsTitle,
          subtitle: l10n.mobileShellGuardsSubtitle,
          icon: Icons.lock_person_outlined,
        ),
      ],
    );
  }
}
