import 'package:flutter/material.dart';

class InsuranceScreen extends StatelessWidget {
  const InsuranceScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('Insurance')),
        body: ListView(children: const [
          Card(
            child: ListTile(
              leading: Icon(Icons.shield_moon),
              title: Text('BUPA Gold · Family'),
              subtitle: Text('Policy BUP-2024-887421 · Valid 2026-12-31'),
            ),
          ),
        ]),
      );
}
