import 'dart:math';

import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../widgets/brand_banner.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({
    required this.busy,
    required this.messageKey,
    required this.onLogin,
    super.key,
  });

  final bool busy;
  final String? messageKey;
  final Future<void> Function({
    required String tenantCode,
    required String identifier,
    required String password,
    required String deviceLabel,
    required String deviceId,
  })
  onLogin;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _tenantController = TextEditingController();
  final _identifierController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _tenantController.dispose();
    _identifierController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: ListView(
                children: [
                  BrandBanner(
                    title: l10n.mobileLoginTitle,
                    subtitle: l10n.mobileLoginSubtitle,
                    tenantName: l10n.mobileLoginTenantBanner,
                  ),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              l10n.mobileLoginFormTitle,
                              style: Theme.of(context).textTheme.titleLarge
                                  ?.copyWith(fontWeight: FontWeight.w800),
                            ),
                            const SizedBox(height: 8),
                            Text(l10n.mobileLoginFormSubtitle),
                            const SizedBox(height: 16),
                            if (widget.messageKey != null) ...[
                              Text(
                                l10n.backendMessage(widget.messageKey!),
                                style: TextStyle(
                                  color: Theme.of(context).colorScheme.error,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              const SizedBox(height: 16),
                            ],
                            TextFormField(
                              controller: _tenantController,
                              decoration: InputDecoration(
                                labelText: l10n.mobileLoginTenantLabel,
                              ),
                              validator: (value) =>
                                  (value == null || value.trim().isEmpty)
                                  ? l10n.mobileValidationRequired
                                  : null,
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _identifierController,
                              decoration: InputDecoration(
                                labelText: l10n.mobileLoginIdentifierLabel,
                              ),
                              validator: (value) =>
                                  (value == null || value.trim().isEmpty)
                                  ? l10n.mobileValidationRequired
                                  : null,
                            ),
                            const SizedBox(height: 12),
                            TextFormField(
                              controller: _passwordController,
                              obscureText: true,
                              decoration: InputDecoration(
                                labelText: l10n.mobileLoginPasswordLabel,
                              ),
                              validator: (value) =>
                                  (value == null || value.trim().isEmpty)
                                  ? l10n.mobileValidationRequired
                                  : null,
                            ),
                            const SizedBox(height: 18),
                            FilledButton.icon(
                              onPressed: widget.busy ? null : _submit,
                              icon: widget.busy
                                  ? const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Icon(Icons.login_rounded),
                              label: Text(l10n.mobileLoginSubmit),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    final random = Random();
    await widget.onLogin(
      tenantCode: _tenantController.text.trim(),
      identifier: _identifierController.text.trim(),
      password: _passwordController.text,
      deviceLabel: 'flutter-mobile',
      deviceId: 'device-${random.nextInt(1 << 20)}',
    );
  }
}
