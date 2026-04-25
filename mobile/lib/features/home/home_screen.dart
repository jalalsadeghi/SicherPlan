import 'package:flutter/material.dart';
import 'dart:typed_data';

import '../../api/mobile_backend.dart';
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
    required this.backend,
    super.key,
  });

  final AppConfig config;
  final MobileSessionController controller;
  final MobileBackendGateway backend;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final mobileContext = controller.context!;

    return ShellScaffold(
      children: [
        BrandBanner(
          title: l10n.homeGreeting(
            mobileContext.preferredName ?? mobileContext.fullName,
          ),
          subtitle: l10n.homeHeroIdentity(
            mobileContext.personnelNo,
            mobileContext.fullName,
          ),
          fallbackInitials: _employeeInitials(mobileContext.fullName),
          avatar: _EmployeeHeroAvatar(
            controller: controller,
            backend: backend,
            context: mobileContext,
            fallbackInitials: _employeeInitials(mobileContext.fullName),
          ),
        ),
        HighlightCard(
          title: l10n.offlineReadinessTitle,
          subtitle: l10n.offlineReadinessSubtitle(config.enableOfflineCache),
          icon: Icons.sync_rounded,
        ),
        HighlightCard(
          title: l10n.mobileShellGuardsTitle,
          subtitle: l10n.mobileShellGuardsSubtitle,
          icon: Icons.lock_person_outlined,
        ),
      ],
    );
  }

  static String _employeeInitials(String fullName) {
    final parts = fullName
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .take(2)
        .toList(growable: false);
    if (parts.isEmpty) {
      return '';
    }
    return parts.map((part) => part.substring(0, 1).toUpperCase()).join();
  }
}

class _EmployeeHeroAvatar extends StatefulWidget {
  const _EmployeeHeroAvatar({
    required this.controller,
    required this.backend,
    required this.context,
    required this.fallbackInitials,
  });

  final MobileSessionController controller;
  final MobileBackendGateway backend;
  final EmployeeMobileContext context;
  final String fallbackInitials;

  @override
  State<_EmployeeHeroAvatar> createState() => _EmployeeHeroAvatarState();
}

class _EmployeeHeroAvatarState extends State<_EmployeeHeroAvatar> {
  Future<Uint8List?>? _imageFuture;

  @override
  void initState() {
    super.initState();
    _imageFuture = _loadImage();
  }

  @override
  void didUpdateWidget(covariant _EmployeeHeroAvatar oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.context.photoDocumentId != widget.context.photoDocumentId ||
        oldWidget.context.photoCurrentVersionNo !=
            widget.context.photoCurrentVersionNo) {
      _imageFuture = _loadImage();
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.context.hasProfilePhoto) {
      return _HeroAvatarPlaceholder(initials: widget.fallbackInitials);
    }

    return FutureBuilder<Uint8List?>(
      future: _imageFuture,
      builder: (context, snapshot) {
        if (snapshot.hasData && snapshot.data != null) {
          return Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(18),
              color: Colors.white.withValues(alpha: 0.18),
            ),
            clipBehavior: Clip.antiAlias,
            child: Image.memory(snapshot.data!, fit: BoxFit.cover),
          );
        }
        return _HeroAvatarPlaceholder(initials: widget.fallbackInitials);
      },
    );
  }

  Future<Uint8List?> _loadImage() async {
    final documentId = widget.context.photoDocumentId;
    final versionNo = widget.context.photoCurrentVersionNo;
    if (documentId == null || versionNo == null) {
      return null;
    }
    try {
      final bytes = await widget.controller.withAccessToken(
        (accessToken) => widget.backend.downloadOwnDocument(
          accessToken,
          documentId: documentId,
          versionNo: versionNo,
        ),
      );
      if (!mounted || bytes.isEmpty) {
        return null;
      }
      return Uint8List.fromList(bytes);
    } on MobileApiException {
      return null;
    }
  }
}

class _HeroAvatarPlaceholder extends StatelessWidget {
  const _HeroAvatarPlaceholder({required this.initials});

  final String initials;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 52,
      height: 52,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(18),
      ),
      alignment: Alignment.center,
      child: initials.trim().isNotEmpty
          ? Text(
              initials,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.4,
              ),
            )
          : const Icon(Icons.person_rounded, color: Colors.white, size: 28),
    );
  }
}
