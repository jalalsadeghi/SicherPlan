import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../session/mobile_role.dart';

class RoleSwitcherCard extends StatelessWidget {
  const RoleSwitcherCard({
    required this.selectedRole,
    required this.onRoleChanged,
    super.key,
  });

  final MobileRole selectedRole;
  final ValueChanged<MobileRole?> onRoleChanged;

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
              l10n.roleViewTitle,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 6),
            Text(
              l10n.roleViewSubtitle,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<MobileRole>(
              initialValue: selectedRole,
              decoration: InputDecoration(
                labelText: l10n.activeMobileRoleLabel,
                border: OutlineInputBorder(),
              ),
              items: MobileRole.values
                  .map(
                    (role) => DropdownMenuItem<MobileRole>(
                      value: role,
                      child: Text(l10n.roleLabel(role)),
                    ),
                  )
                  .toList(growable: false),
              onChanged: onRoleChanged,
            ),
            const SizedBox(height: 12),
            Text(
              l10n.roleDescription(selectedRole),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
