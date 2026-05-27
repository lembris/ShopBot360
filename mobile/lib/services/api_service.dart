import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const baseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }

  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', token);
  }

  Future<Map<String, dynamic>> login(String phone, String password) async {
    final res = await http.post(
      Uri.parse('$baseUrl/admin/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'phone': phone, 'password': password}),
    );
    if (res.statusCode != 200) throw Exception('Login failed');
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    await saveToken(data['access_token'] as String);
    return data;
  }

  Future<List<dynamic>> fetchSales() async {
    final token = await getToken();
    final res = await http.get(
      Uri.parse('$baseUrl/admin/sales'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load sales');
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> fetchReports() async {
    final token = await getToken();
    final res = await http.get(
      Uri.parse('$baseUrl/admin/reports'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load reports');
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> fetchProducts() async {
    final token = await getToken();
    final res = await http.get(
      Uri.parse('$baseUrl/admin/products'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode != 200) throw Exception('Failed to load products');
    return jsonDecode(res.body) as List<dynamic>;
  }
}
