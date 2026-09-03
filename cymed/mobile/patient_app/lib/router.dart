import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'auth/screens/splash_screen.dart';
import 'auth/screens/login_screen.dart';
import 'auth/screens/otp_screen.dart';
import 'auth/screens/biometric_setup_screen.dart';
import 'records/home_screen.dart';
import 'records/timeline_screen.dart';
import 'records/lab_result_screen.dart';
import 'records/imaging_viewer_screen.dart';
import 'records/prescriptions_screen.dart';
import 'appointments/appointments_screen.dart';
import 'nfc/nfc_home_screen.dart';
import 'nfc/emergency_profile_screen.dart';
import 'delegated/family_screen.dart';
import 'payments/bills_screen.dart';
import 'payments/insurance_screen.dart';
import 'consent/consent_screen.dart';

GoRouter buildRouter() => GoRouter(
      initialLocation: '/',
      routes: [
        GoRoute(path: '/',                     builder: (_, __) => const SplashScreen()),
        GoRoute(path: '/login',                builder: (_, __) => const LoginScreen()),
        GoRoute(path: '/otp',                  builder: (_, __) => const OtpScreen()),
        GoRoute(path: '/biometric-setup',      builder: (_, __) => const BiometricSetupScreen()),
        GoRoute(path: '/home',                 builder: (_, __) => const HomeScreen()),
        GoRoute(path: '/timeline',             builder: (_, __) => const TimelineScreen()),
        GoRoute(path: '/labs/:id',             builder: (c, s) => LabResultScreen(id: s.pathParameters['id']!)),
        GoRoute(path: '/imaging/:id',          builder: (c, s) => ImagingViewerScreen(id: s.pathParameters['id']!)),
        GoRoute(path: '/prescriptions',        builder: (_, __) => const PrescriptionsScreen()),
        GoRoute(path: '/appointments',         builder: (_, __) => const AppointmentsScreen()),
        GoRoute(path: '/nfc',                  builder: (_, __) => const NfcHomeScreen()),
        GoRoute(path: '/emergency',            builder: (_, __) => const EmergencyProfileScreen()),
        GoRoute(path: '/family',               builder: (_, __) => const FamilyScreen()),
        GoRoute(path: '/bills',                builder: (_, __) => const BillsScreen()),
        GoRoute(path: '/insurance',            builder: (_, __) => const InsuranceScreen()),
        GoRoute(path: '/consent',              builder: (_, __) => const ConsentScreen()),
      ],
    );
