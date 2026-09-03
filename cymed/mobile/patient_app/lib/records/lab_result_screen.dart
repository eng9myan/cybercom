import 'package:flutter/material.dart';

class LabResultScreen extends StatelessWidget {
  const LabResultScreen({required this.id, super.key});
  final String id;
  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: Text('Lab Result $id')),
        body: const Center(child: Text('Report + trend chart (fl_chart) — data via /records/labs/{id}')),
      );
}
