import 'package:flutter/material.dart';

import '../../config/app_config.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_role.dart';
import '../../session/mobile_session.dart';
import '../../widgets/brand_banner.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/role_switcher_card.dart';
import '../../widgets/shell_scaffold.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    required this.config,
    required this.session,
    required this.onRoleChanged,
    super.key,
  });

  final AppConfig config;
  final MobileSession session;
  final ValueChanged<MobileRole?> onRoleChanged;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return ShellScaffold(
      title: l10n.homeTitle,
      subtitle: l10n.homeSubtitle,
      children: [
        BrandBanner(
          title: l10n.homeGreeting(session.userName),
          subtitle: l10n.homeBannerSubtitle,
          tenantName: session.tenantName,
          trailing: session.offlineReady
              ? const Icon(Icons.cloud_done_rounded, color: Colors.white)
              : const Icon(Icons.cloud_off_rounded, color: Colors.white),
        ),
        RoleSwitcherCard(
          selectedRole: session.role,
          onRoleChanged: onRoleChanged,
        ),
        HighlightCard(
          title: l10n.todayReleasedTitle,
          subtitle: l10n.todayReleasedSubtitle,
          icon: Icons.assignment_turned_in_outlined,
          badge: l10n.roleLabel(session.role),
        ),
        HighlightCard(
          title: l10n.offlineReadinessTitle,
          subtitle: l10n.offlineReadinessSubtitle(config.enableOfflineCache),
          icon: Icons.sync_rounded,
          badge: config.env,
        ),
      ],
    );
  }
}
