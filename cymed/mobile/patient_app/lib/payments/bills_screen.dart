import 'package:flutter/material.dart';

class BillsScreen extends StatelessWidget {
  const BillsScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('Bills')),
        body: ListView(children: [
          Card(
            child: ListTile(
              title: const Text('Riyadh Hospital · ICU 3 nights'),
              subtitle: const Text('Insurance paid SAR 3,200 · You owe SAR 800'),
              trailing: FilledButton(onPressed: () {}, child: const Text('Pay')),
            ),
          ),
        ]),
      );
}
