import 'package:flutter/material.dart';

class PrescriptionsScreen extends StatelessWidget {
  const PrescriptionsScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('Prescriptions')),
        body: ListView(children: [
          ListTile(
            leading: const CircleAvatar(child: Icon(Icons.medication)),
            title: const Text('Atorvastatin 40mg'),
            subtitle: const Text('1 tablet daily · 2 refills left'),
            trailing: TextButton(onPressed: () {}, child: const Text('Refill')),
          ),
        ]),
      );
}
