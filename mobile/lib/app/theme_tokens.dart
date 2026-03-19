import 'package:flutter/material.dart';

class SicherPlanThemeTokens {
  const SicherPlanThemeTokens({
    required this.mode,
    required this.primary,
    required this.primaryStrong,
    required this.primaryMuted,
    required this.success,
    required this.warning,
    required this.danger,
    required this.surfacePage,
    required this.surfacePanel,
    required this.surfaceCard,
    required this.borderSoft,
    required this.textPrimary,
    required this.textSecondary,
    required this.textInverse,
  });

  final ThemeMode mode;
  final Color primary;
  final Color primaryStrong;
  final Color primaryMuted;
  final Color success;
  final Color warning;
  final Color danger;
  final Color surfacePage;
  final Color surfacePanel;
  final Color surfaceCard;
  final Color borderSoft;
  final Color textPrimary;
  final Color textSecondary;
  final Color textInverse;

  static SicherPlanThemeTokens light() {
    return const SicherPlanThemeTokens(
      mode: ThemeMode.light,
      primary: Color.fromRGBO(40, 170, 170, 1),
      primaryStrong: Color.fromRGBO(17, 111, 111, 1),
      primaryMuted: Color.fromRGBO(40, 170, 170, 0.14),
      success: Color.fromRGBO(46, 148, 110, 1),
      warning: Color.fromRGBO(194, 137, 37, 1),
      danger: Color.fromRGBO(185, 78, 78, 1),
      surfacePage: Color(0xFFF4F7F8),
      surfacePanel: Color.fromRGBO(255, 255, 255, 0.82),
      surfaceCard: Colors.white,
      borderSoft: Color.fromRGBO(21, 74, 75, 0.12),
      textPrimary: Color.fromRGBO(24, 53, 53, 1),
      textSecondary: Color.fromRGBO(70, 100, 100, 1),
      textInverse: Color.fromRGBO(238, 248, 247, 1),
    );
  }

  static SicherPlanThemeTokens dark() {
    return const SicherPlanThemeTokens(
      mode: ThemeMode.dark,
      primary: Color.fromRGBO(35, 200, 205, 1),
      primaryStrong: Color.fromRGBO(18, 123, 128, 1),
      primaryMuted: Color.fromRGBO(35, 200, 205, 0.18),
      success: Color.fromRGBO(79, 186, 141, 1),
      warning: Color.fromRGBO(225, 178, 74, 1),
      danger: Color.fromRGBO(222, 111, 111, 1),
      surfacePage: Color(0xFF081214),
      surfacePanel: Color.fromRGBO(18, 32, 35, 0.88),
      surfaceCard: Color.fromRGBO(18, 32, 35, 0.94),
      borderSoft: Color.fromRGBO(203, 241, 242, 0.12),
      textPrimary: Color.fromRGBO(230, 245, 245, 1),
      textSecondary: Color.fromRGBO(151, 181, 182, 1),
      textInverse: Color.fromRGBO(8, 18, 20, 1),
    );
  }
}
