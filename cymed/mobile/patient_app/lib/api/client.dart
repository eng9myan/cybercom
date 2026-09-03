import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Central API client for CyMed Patient App.
/// Base URL is per-environment; injected from --dart-define=CYMED_API_URL=...
class CyMedApiClient {
  CyMedApiClient({String? baseUrl})
      : dio = Dio(BaseOptions(
          baseUrl: baseUrl ?? const String.fromEnvironment(
            'CYMED_API_URL',
            defaultValue: 'https://sandbox.cymed.sa/api/v1/patient-app',
          ),
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 30),
          headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
        )) {
    dio.interceptors.add(_AuthInterceptor());
  }

  final Dio dio;
  static const _storage = FlutterSecureStorage();
  static const _kAccess = 'cymed.access';
  static const _kRefresh = 'cymed.refresh';

  static Future<void> setTokens(String access, String refresh) async {
    await _storage.write(key: _kAccess, value: access);
    await _storage.write(key: _kRefresh, value: refresh);
  }

  static Future<void> clear() async {
    await _storage.delete(key: _kAccess);
    await _storage.delete(key: _kRefresh);
  }

  static Future<String?> access() => _storage.read(key: _kAccess);
}

class _AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler h) async {
    final t = await CyMedApiClient.access();
    if (t != null) options.headers['Authorization'] = 'Bearer $t';
    h.next(options);
  }
}
