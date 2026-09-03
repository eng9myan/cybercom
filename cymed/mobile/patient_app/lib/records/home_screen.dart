import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/colors.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('CyMed'),
          actions: [
            IconButton(onPressed: () {}, icon: const Icon(Icons.notifications_none)),
          ],
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: CyMedColors.brandGradient,
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Welcome back', style: TextStyle(color: Colors.white70)),
                    SizedBox(height: 4),
                    Text('Your health at a glance',
                        style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              GridView.count(
                crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12, crossAxisSpacing: 12,
                children: [
                  _tile(context, Icons.timeline_rounded, 'Records',      '/timeline'),
                  _tile(context, Icons.event_available,  'Appointments', '/appointments'),
                  _tile(context, Icons.medication,       'Prescriptions','/prescriptions'),
                  _tile(context, Icons.nfc,              'NFC Card',     '/nfc'),
                  _tile(context, Icons.local_hospital,   'Emergency',    '/emergency'),
                  _tile(context, Icons.family_restroom,  'Family',       '/family'),
                  _tile(context, Icons.receipt_long,     'Bills',        '/bills'),
                  _tile(context, Icons.shield_moon,      'Insurance',    '/insurance'),
                ],
              ),
            ],
          ),
        ),
      );

  Widget _tile(BuildContext c, IconData i, String label, String path) => Card(
        child: InkWell(
          onTap: () => c.push(path),
          borderRadius: BorderRadius.circular(20),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(i, size: 36),
                const SizedBox(height: 12),
                Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ),
      );
}
