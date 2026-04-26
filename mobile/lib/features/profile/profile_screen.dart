import 'package:flutter/material.dart';

import '../../api/mobile_backend.dart';
import '../../config/app_config.dart';
import '../../l10n/app_localizations.dart';
import '../../session/mobile_session_controller.dart';
import '../../widgets/highlight_card.dart';
import '../../widgets/locale_card.dart';
import '../../widgets/shell_scaffold.dart';
import '../../widgets/theme_mode_card.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({
    required this.config,
    required this.controller,
    required this.backend,
    required this.themeMode,
    required this.locale,
    required this.onThemeModeChanged,
    required this.onLocaleChanged,
    super.key,
  });

  final AppConfig config;
  final MobileSessionController controller;
  final MobileBackendGateway backend;
  final ThemeMode themeMode;
  final Locale locale;
  final ValueChanged<ThemeMode> onThemeModeChanged;
  final ValueChanged<Locale> onLocaleChanged;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late Future<List<EmployeeMobileCredential>> _credentialsFuture;

  @override
  void initState() {
    super.initState();
    _credentialsFuture = _loadCredentials();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final mobileContext = widget.controller.context!;

    return ShellScaffold(
      title: l10n.profileTitle,
      subtitle: l10n.profileSubtitle,
      children: [
        ThemeModeCard(
          themeMode: widget.themeMode,
          onChanged: widget.onThemeModeChanged,
        ),
        LocaleCard(
          locale: widget.locale,
          onChanged: (value) {
            if (value != null) {
              widget.onLocaleChanged(value);
            }
          },
        ),
        HighlightCard(
          title: mobileContext.fullName,
          subtitle: l10n.profileRoleSubtitle(
            mobileContext.tenantId,
            mobileContext.appRole,
          ),
          icon: Icons.account_circle_outlined,
        ),
        FutureBuilder<List<EmployeeMobileCredential>>(
          future: _credentialsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const Padding(
                padding: EdgeInsets.symmetric(vertical: 20),
                child: Center(child: CircularProgressIndicator()),
              );
            }
            if (snapshot.hasError) {
              return HighlightCard(
                title: l10n.credentialsErrorTitle,
                subtitle: l10n.mobileLoadErrorSubtitle(snapshot.error),
                icon: Icons.error_outline_rounded,
              );
            }
            final items = snapshot.data ?? const [];
            if (items.isEmpty) {
              return HighlightCard(
                title: l10n.credentialsEmptyTitle,
                subtitle: l10n.credentialsEmptySubtitle,
                icon: Icons.badge_outlined,
              );
            }
            return Card(
              margin: const EdgeInsets.only(bottom: 14),
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l10n.credentialsTitle,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ...items.map((item) => _CredentialCard(item: item)),
                  ],
                ),
              ),
            );
          },
        ),
        HighlightCard(
          title: l10n.environmentTitle,
          subtitle: l10n.apiSubtitle(widget.config.apiBaseUrl),
          icon: Icons.settings_ethernet_rounded,
          badge: widget.config.env,
        ),
        FilledButton.icon(
          onPressed: widget.controller.logout,
          icon: const Icon(Icons.logout_rounded),
          label: Text(l10n.mobileLogoutAction),
        ),
      ],
    );
  }

  Future<List<EmployeeMobileCredential>> _loadCredentials() {
    return widget.controller.withAccessToken(widget.backend.fetchCredentials);
  }
}

class _CredentialCard extends StatelessWidget {
  const _CredentialCard({required this.item});

  final EmployeeMobileCredential item;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.08),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            item.credentialNo,
            style: Theme.of(
              context,
            ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 6),
          Text(item.credentialType),
          const SizedBox(height: 12),
          SizedBox(
            height: 72,
            child: CustomPaint(
              painter: _PseudoBarcodePainter(item.encodedValue),
              child: Center(
                child: Text(
                  item.encodedValue,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    backgroundColor: Theme.of(context).colorScheme.surface,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PseudoBarcodePainter extends CustomPainter {
  _PseudoBarcodePainter(this.value);

  final String value;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = Colors.black87;
    final bytes = value.codeUnits;
    final segments = (bytes.length * 2).clamp(1, 9999).toDouble();
    final barWidth = size.width / segments;
    for (var i = 0; i < bytes.length; i++) {
      final normalized = (bytes[i] % 5) + 1;
      final left = i * barWidth * 2;
      canvas.drawRect(
        Rect.fromLTWH(left, 8, barWidth * normalized / 2, size.height - 16),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _PseudoBarcodePainter oldDelegate) =>
      oldDelegate.value != value;
}
