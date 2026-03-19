import 'package:flutter/material.dart';

import 'theme_tokens.dart';

ThemeData buildSicherPlanTheme({required SicherPlanThemeTokens tokens}) {
  final baseScheme = ColorScheme.fromSeed(
    seedColor: tokens.primary,
    brightness: tokens.mode == ThemeMode.dark
        ? Brightness.dark
        : Brightness.light,
  );

  return ThemeData(
    useMaterial3: true,
    brightness: tokens.mode == ThemeMode.dark
        ? Brightness.dark
        : Brightness.light,
    colorScheme: baseScheme.copyWith(
      primary: tokens.primary,
      secondary: tokens.primary,
      surface: tokens.surfacePage,
      outlineVariant: tokens.borderSoft,
      onSurface: tokens.textPrimary,
      onPrimary: tokens.textInverse,
      error: tokens.danger,
    ),
    scaffoldBackgroundColor: tokens.surfacePage,
    dividerColor: tokens.borderSoft,
    cardTheme: CardThemeData(
      color: tokens.surfaceCard,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      margin: EdgeInsets.zero,
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.transparent,
      foregroundColor: tokens.textPrimary,
      elevation: 0,
      centerTitle: false,
    ),
    textTheme: TextTheme(
      headlineSmall: TextStyle(color: tokens.textPrimary),
      titleLarge: TextStyle(color: tokens.textPrimary),
      titleMedium: TextStyle(color: tokens.textPrimary),
      bodyLarge: TextStyle(color: tokens.textPrimary),
      bodyMedium: TextStyle(color: tokens.textSecondary),
      bodySmall: TextStyle(color: tokens.textSecondary),
      labelLarge: TextStyle(color: tokens.textPrimary),
      labelMedium: TextStyle(color: tokens.textSecondary),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: tokens.surfaceCard,
      indicatorColor: tokens.primaryMuted,
      iconTheme: WidgetStateProperty.resolveWith((states) {
        final selected = states.contains(WidgetState.selected);
        return IconThemeData(
          color: selected ? tokens.primary : tokens.textSecondary,
        );
      }),
      labelTextStyle: WidgetStateProperty.resolveWith((states) {
        final selected = states.contains(WidgetState.selected);
        return TextStyle(
          fontSize: 12,
          fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
          color: selected ? tokens.primary : tokens.textSecondary,
        );
      }),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: tokens.surfaceCard,
      labelStyle: TextStyle(color: tokens.textSecondary),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: tokens.borderSoft),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: tokens.borderSoft),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: tokens.primary),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: tokens.primaryMuted,
      selectedColor: tokens.primaryMuted,
      side: BorderSide.none,
      labelStyle: TextStyle(color: tokens.primaryStrong),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
    ),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: tokens.primary,
      foregroundColor: tokens.textInverse,
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return tokens.primary;
        }
        return tokens.textSecondary;
      }),
      trackColor: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return tokens.primaryMuted;
        }
        return tokens.borderSoft;
      }),
    ),
    listTileTheme: ListTileThemeData(
      iconColor: tokens.primary,
      textColor: tokens.textPrimary,
    ),
  );
}

ThemeData resolveSicherPlanTheme({
  required ThemeMode mode,
  required String lightPrimaryConfig,
  required String darkPrimaryConfig,
}) {
  if (mode == ThemeMode.dark) {
    final tokens = SicherPlanThemeTokens.dark();
    return buildSicherPlanTheme(
      tokens: SicherPlanThemeTokens(
        mode: tokens.mode,
        primary: parseConfiguredPrimary(
          darkPrimaryConfig,
          fallbackMode: ThemeMode.dark,
        ),
        primaryStrong: tokens.primaryStrong,
        primaryMuted: tokens.primaryMuted,
        success: tokens.success,
        warning: tokens.warning,
        danger: tokens.danger,
        surfacePage: tokens.surfacePage,
        surfacePanel: tokens.surfacePanel,
        surfaceCard: tokens.surfaceCard,
        borderSoft: tokens.borderSoft,
        textPrimary: tokens.textPrimary,
        textSecondary: tokens.textSecondary,
        textInverse: tokens.textInverse,
      ),
    );
  }

  final tokens = SicherPlanThemeTokens.light();
  return buildSicherPlanTheme(
    tokens: SicherPlanThemeTokens(
      mode: tokens.mode,
      primary: parseConfiguredPrimary(
        lightPrimaryConfig,
        fallbackMode: ThemeMode.light,
      ),
      primaryStrong: tokens.primaryStrong,
      primaryMuted: tokens.primaryMuted,
      success: tokens.success,
      warning: tokens.warning,
      danger: tokens.danger,
      surfacePage: tokens.surfacePage,
      surfacePanel: tokens.surfacePanel,
      surfaceCard: tokens.surfaceCard,
      borderSoft: tokens.borderSoft,
      textPrimary: tokens.textPrimary,
      textSecondary: tokens.textSecondary,
      textInverse: tokens.textInverse,
    ),
  );
}

Color parseConfiguredPrimary(String value, {required ThemeMode fallbackMode}) {
  final parsed = parseRgbColor(value);
  final required = fallbackMode == ThemeMode.dark
      ? const Color.fromRGBO(35, 200, 205, 1)
      : const Color.fromRGBO(40, 170, 170, 1);

  return parsed == required ? parsed : required;
}

Color parseRgbColor(String value) {
  final channels = value
      .split(',')
      .map((entry) => int.tryParse(entry.trim()))
      .toList(growable: false);

  if (channels.length != 3 || channels.any((channel) => channel == null)) {
    return const Color.fromRGBO(40, 170, 170, 1);
  }

  return Color.fromRGBO(channels[0]!, channels[1]!, channels[2]!, 1);
}
