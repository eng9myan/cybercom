import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:google_fonts/google_fonts.dart';
import 'router.dart';
import 'theme/colors.dart';

class CyMedPatientApp extends StatelessWidget {
  const CyMedPatientApp({super.key});

  @override
  Widget build(BuildContext context) {
    final router = buildRouter();
    return MaterialApp.router(
      title: 'CyMed',
      routerConfig: router,
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.system,
      theme: _buildTheme(Brightness.light),
      darkTheme: _buildTheme(Brightness.dark),
      supportedLocales: const [Locale('ar'), Locale('en')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      locale: const Locale('ar'),
    );
  }

  ThemeData _buildTheme(Brightness b) {
    final scheme = b == Brightness.dark
        ? const ColorScheme.dark(
            primary: CyMedColors.brandPrimary,
            secondary: CyMedColors.accent,
            surface: CyMedColors.surfaceDark,
          )
        : const ColorScheme.light(
            primary: CyMedColors.brandPrimary,
            secondary: CyMedColors.accent,
            surface: Colors.white,
          );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: b == Brightness.dark
          ? CyMedColors.backgroundDark
          : CyMedColors.backgroundLight,
      textTheme: GoogleFonts.spaceGroteskTextTheme(
        b == Brightness.dark ? ThemeData.dark().textTheme : ThemeData.light().textTheme,
      ),
      cardTheme: const CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(20))),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
    );
  }
}
