import 'package:flutter/material.dart';

class ConsentScreen extends StatelessWidget {
  const ConsentScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('Consent')),
        body: ListView(children: const [
          SwitchListTile(
            value: true, onChanged: null,
            title: Text('Riyadh Hospital — Treatment'),
            subtitle: Text('Full records · Valid until 2027-01-01'),
          ),
        ]),
      );
}
