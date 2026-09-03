import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class NfcHomeScreen extends StatelessWidget {
  const NfcHomeScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('My NFC Card')),
        body: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(children: [
                  const Icon(Icons.credit_card, size: 64),
                  const SizedBox(height: 12),
                  const Text('Active · Last scanned yesterday at Riyadh Hospital'),
                  const SizedBox(height: 12),
                  Wrap(spacing: 8, children: [
                    OutlinedButton(onPressed: () {}, child: const Text('Suspend')),
                    ElevatedButton(onPressed: () => c.push('/emergency'), child: const Text('Emergency Profile')),
                  ]),
                ]),
              ),
            ),
            const SizedBox(height: 16),
            const Card(
              child: ListTile(
                leading: Icon(Icons.history),
                title: Text('Recent scans'),
                subtitle: Text('Provider · purpose · time'),
              ),
            ),
          ]),
        ),
      );
}
