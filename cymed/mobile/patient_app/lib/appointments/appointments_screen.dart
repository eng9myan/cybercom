import 'package:flutter/material.dart';

class AppointmentsScreen extends StatelessWidget {
  const AppointmentsScreen({super.key});
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('Appointments')),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: () {}, icon: const Icon(Icons.add), label: const Text('Book'),
        ),
        body: ListView(children: [
          ListTile(
            leading: const Icon(Icons.calendar_today),
            title: const Text('Dr Al-Otaibi · Cardiology'),
            subtitle: const Text('Tomorrow · 10:00'),
          ),
        ]),
      );
}
