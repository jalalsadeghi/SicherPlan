import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';

class LocaleCard extends StatelessWidget {
  const LocaleCard({required this.locale, required this.onChanged, super.key});

  final Locale locale;
  final ValueChanged<Locale?> onChanged;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.localeCardTitle,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 6),
            Text(
              l10n.localeCardSubtitle,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<Locale>(
              initialValue: Locale(locale.languageCode),
              decoration: InputDecoration(
                labelText: l10n.localeLabel,
                border: const OutlineInputBorder(),
              ),
              items: [
                DropdownMenuItem(
                  value: const Locale('de'),
                  child: Text(l10n.localeGerman),
                ),
                DropdownMenuItem(
                  value: const Locale('en'),
                  child: Text(l10n.localeEnglish),
                ),
              ],
              onChanged: onChanged,
            ),
          ],
        ),
      ),
    );
  }
}
