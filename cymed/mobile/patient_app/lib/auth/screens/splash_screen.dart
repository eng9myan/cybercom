import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../api/client.dart';
import '../../theme/colors.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    await Future.delayed(const Duration(milliseconds: 900));
    final token = await CyMedApiClient.access();
    if (!mounted) return;
    context.go(token != null ? '/home' : '/login');
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: Container(
          decoration: const BoxDecoration(gradient: CyMedColors.brandGradient),
          child: const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.local_hospital_rounded, size: 96, color: Colors.white),
                SizedBox(height: 16),
                Text('CyMed',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 40,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 2,
                    )),
                SizedBox(height: 8),
                Text('Your health, one tap away.',
                    style: TextStyle(color: Colors.white70)),
              ],
            ),
          ),
        ),
      );
}
