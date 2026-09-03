import 'package:flutter/material.dart';

/// CyMed brand palette — matches web design system.
class CyMedColors {
  static const backgroundDark = Color(0xFF0A0E27);
  static const backgroundLight = Color(0xFFF7F8FB);
  static const surfaceDark = Color(0xFF141A3D);
  static const brandPrimary = Color(0xFF0062CC);
  static const accent = Color(0xFF00D4AA);
  static const danger = Color(0xFFEF4444);
  static const warning = Color(0xFFF39C12);
  static const success = Color(0xFF10B981);

  /// Cybercom blue → accent teal gradient used in headers.
  static const brandGradient = LinearGradient(
    colors: [Color(0xFF0062CC), Color(0xFF00D4AA)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}
