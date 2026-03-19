import 'package:flutter/material.dart';

import '../../config/app_config.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/locale_card.dart';
import '../../widgets/shell_scaffold.dart';
import '../../widgets/theme_mode_card.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({
    required this.config,
    required this.session,
    required this.themeMode,
    required this.locale,
    required this.onThemeModeChanged,
    required this.onLocaleChanged,
    super.key,
  });

  final AppConfig config;
  final MobileSession session;
  final ThemeMode themeMode;
  final Locale locale;
  final ValueChanged<ThemeMode> onThemeModeChanged;
  final ValueChanged<Locale> onLocaleChanged;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return ShellScaffold(
      title: l10n.profileTitle,
      subtitle: l10n.profileSubtitle,
      children: [
        ThemeModeCard(themeMode: themeMode, onChanged: onThemeModeChanged),
        LocaleCard(
          locale: locale,
          onChanged: (value) {
            if (value != null) {
              onLocaleChanged(value);
            }
          },
        ),
        HighlightCard(
          title: session.userName,
          subtitle: l10n.profileRoleSubtitle(
            session.tenantName,
            l10n.roleLabel(session.role),
          ),
          icon: Icons.account_circle_outlined,
        ),
        HighlightCard(
          title: l10n.languageBaselineTitle,
          subtitle: l10n.languageBaselineSubtitle(
            config.defaultLocale,
            config.fallbackLocale,
          ),
          icon: Icons.language_rounded,
        ),
        HighlightCard(
          title: l10n.environmentTitle,
          subtitle: l10n.apiSubtitle(config.apiBaseUrl),
          icon: Icons.settings_ethernet_rounded,
          badge: config.env,
        ),
      ],
    );
  }
}
