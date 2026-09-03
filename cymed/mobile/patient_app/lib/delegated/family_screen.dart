import 'package:flutter/material.dart';

class FamilyScreen extends StatelessWidget {
  const FamilyScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('Family')),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: () {}, icon: const Icon(Icons.person_add), label: const Text('Invite'),
        ),
        body: ListView(children: const [
          ListTile(
            leading: CircleAvatar(child: Text('M')),
            title: Text('Mother — Fatima'),
            subtitle: Text('Records · Book appt · Pay bills'),
          ),
        ]),
      );
}
