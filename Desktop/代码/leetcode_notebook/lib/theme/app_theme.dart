import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Colors
  static const bgDeep    = Color(0xFF0D1B2A);
  static const bgCard    = Color(0xFF112233);
  static const bgCardBack = Color(0xFF162840);
  static const bgSheet   = Color(0xFF0F1E2E);
  static const blue      = Color(0xFF5BA4CF);  // 冷雾蓝（偏灰，低饱和）
  static const green     = Color(0xFF4A9E82);  // 暗青绿（冷调，低饱和）
  static const orange    = Color(0xFFFF6B35);
  static const textPrimary   = Color(0xFFE8F4FD);
  static const textSecondary = Color(0xFF7A9BB5);
  static const gridLine  = Color(0xFF1A2E42);
  static const borderLine = Color(0xFF1A3A5C);

  // Difficulty colors
  static Color difficultyColor(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'easy':   return green;
      case 'medium': return blue;
      case 'hard':   return orange;
      default:       return textSecondary;
    }
  }

  // Typography
  static TextStyle pixelStyle({double size = 12, Color color = textPrimary}) {
    try {
      return GoogleFonts.pressStart2p(fontSize: size, color: color);
    } catch (_) {
      return TextStyle(fontFamily: 'monospace', fontSize: size, color: color);
    }
  }

  static TextStyle monoStyle({double size = 14, Color color = textPrimary, FontWeight weight = FontWeight.normal}) {
    try {
      return GoogleFonts.jetBrainsMono(fontSize: size, color: color, fontWeight: weight);
    } catch (_) {
      return TextStyle(fontFamily: 'monospace', fontSize: size, color: color, fontWeight: weight);
    }
  }

  static TextStyle pixelNumberStyle({
    double size = 14,
    Color color = textPrimary,
    FontWeight weight = FontWeight.normal
  }) {
    try {
      return GoogleFonts.silkscreen(
        fontSize: size,
        color: color,
        fontWeight: weight,
      );
    } catch (_) {
      return TextStyle(
        fontFamily: 'monospace',
        fontSize: size,
        color: color,
        fontWeight: weight,
      );
    }
  }

  // Pixel border decoration
  static BoxDecoration pixelBorder({Color borderColor = blue, Color? glowColor}) {
    final glow = glowColor ?? blue;
    return BoxDecoration(
      border: Border.all(color: borderColor, width: 3),
      boxShadow: [
        // 近层：蓝色光晕
        BoxShadow(color: glow.withValues(alpha: 0.30), blurRadius: 15, spreadRadius: 0),
        // 中层：柔和扩散
        BoxShadow(color: glow.withValues(alpha: 0.10), blurRadius: 30, spreadRadius: 5),
        // 远层：深度阴影
        BoxShadow(color: const Color(0x66000000), blurRadius: 40, offset: const Offset(0, 10)),
      ],
    );
  }

  // 翻转激活时使用——光晕增强版
  static BoxDecoration glassBorderActive({Color borderColor = blue}) {
    return BoxDecoration(
      border: Border.all(color: borderColor, width: 3),
      boxShadow: [
        BoxShadow(color: borderColor.withValues(alpha: 0.60), blurRadius: 15, spreadRadius: 2),
        BoxShadow(color: borderColor.withValues(alpha: 0.20), blurRadius: 30, spreadRadius: 8),
        BoxShadow(color: const Color(0x66000000), blurRadius: 40, offset: const Offset(0, 10)),
      ],
    );
  }

  // ThemeData
  static ThemeData get theme => ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: bgDeep,
    colorScheme: const ColorScheme.dark(
      surface: bgDeep,
      primary: blue,
      secondary: green,
      onSurface: textPrimary,
      outline: borderLine,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: bgDeep,
      foregroundColor: textPrimary,
      elevation: 0,
      surfaceTintColor: Colors.transparent,
    ),
    chipTheme: ChipThemeData(
      backgroundColor: bgCard,
      selectedColor: Color(0x4D00B4FF),
      labelStyle: monoStyle(size: 11),
      side: const BorderSide(color: blue, width: 1),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: bgSheet,
      modalBackgroundColor: bgSheet,
    ),
    dividerColor: gridLine,
    textTheme: TextTheme(
      bodyMedium: TextStyle(fontFamily: 'monospace', fontSize: 13, color: textPrimary),
      bodySmall: TextStyle(fontFamily: 'monospace', fontSize: 11, color: textSecondary),
    ),
  );
}
