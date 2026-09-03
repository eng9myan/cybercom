import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class ImagingViewerScreen extends StatefulWidget {
  const ImagingViewerScreen({required this.id, super.key});
  final String id;
  @override
  State<ImagingViewerScreen> createState() => _S();
}

class _S extends State<ImagingViewerScreen> {
  late final WebViewController _wv;
  @override
  void initState() {
    super.initState();
    _wv = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(Uri.parse('about:blank'));   // real: fetch signed OHIF viewer URL
  }

  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: Text('Imaging ${widget.id}')),
        body: WebViewWidget(controller: _wv),
      );
}
