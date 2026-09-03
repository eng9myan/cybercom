import 'package:flutter/material.dart';

class EmergencyProfileScreen extends StatelessWidget {
  const EmergencyProfileScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('Emergency Profile')),
        body: ListView(padding: const EdgeInsets.all(20), children: const [
          ListTile(leading: Icon(Icons.bloodtype), title: Text('Blood type'), subtitle: Text('A+')),
          Divider(),
          ListTile(leading: Icon(Icons.warning_amber), title: Text('Allergies'), subtitle: Text('Penicillin (severe)')),
          Divider(),
          ListTile(leading: Icon(Icons.medication), title: Text('Meds'), subtitle: Text('Atorvastatin 40mg QD')),
          Divider(),
          ListTile(leading: Icon(Icons.phone), title: Text('Emergency contact'), subtitle: Text('Ahmad — spouse — +9665...')),
        ]),
      );
}
