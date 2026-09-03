import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../api/client.dart';

class OtpScreen extends StatefulWidget {
  const OtpScreen({super.key});
  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final _otp = TextEditingController();
  bool _loading = false;

  Future<void> _verify() async {
    setState(() => _loading = true);
    try {
      final r = await CyMedApiClient().dio.post('/auth/verify-otp',
          data: {'phone': '', 'otp': _otp.text.trim()});
      await CyMedApiClient.setTokens(r.data['access_token'], r.data['refresh_token']);
      if (!mounted) return;
      context.go(r.data['needs_biometric_setup'] == true ? '/biometric-setup' : '/home');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Verify OTP')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(children: [
            TextField(controller: _otp, keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Enter 6-digit OTP', border: OutlineInputBorder())),
            const SizedBox(height: 24),
            ElevatedButton(onPressed: _loading ? null : _verify, child: const Text('Verify')),
          ]),
        ),
      );
}
