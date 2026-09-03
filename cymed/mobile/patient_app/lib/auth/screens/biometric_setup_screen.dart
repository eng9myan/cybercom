import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart';

class BiometricSetupScreen extends StatelessWidget {
  const BiometricSetupScreen({super.key});

  Future<void> _enable(BuildContext context) async {
    final auth = LocalAuthentication();
    final ok = await auth.authenticate(
      localizedReason: 'Enable biometric sign-in',
      options: const AuthenticationOptions(biometricOnly: true, stickyAuth: true),
    );
    if (context.mounted && ok) context.go('/home');
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Secure your app')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.fingerprint, size: 96),
              const SizedBox(height: 24),
              const Text('Enable Face ID / Fingerprint for faster and safer access.',
                  textAlign: TextAlign.center),
              const SizedBox(height: 32),
              ElevatedButton(onPressed: () => _enable(context), child: const Text('Enable')),
              TextButton(onPressed: () => context.go('/home'), child: const Text('Skip')),
            ],
          ),
        ),
      );
}
