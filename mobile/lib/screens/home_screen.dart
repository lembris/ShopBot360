import 'package:flutter/material.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = ApiService();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _loggedIn = false;
  String _reportToday = '';
  List<dynamic> _sales = [];
  List<dynamic> _lowStock = [];

  Future<void> _login() async {
    await _api.login(_phoneController.text, _passwordController.text);
    setState(() => _loggedIn = true);
    await _loadData();
  }

  Future<void> _loadData() async {
    final reports = await _api.fetchReports();
    final sales = await _api.fetchSales();
    final products = await _api.fetchProducts();
    setState(() {
      _reportToday = reports['today']?.toString() ?? '';
      _sales = sales;
      _lowStock = products
          .where((p) => (p['stock_qty'] as int) <= (p['reorder_at'] as int? ?? 5))
          .toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_loggedIn) {
      return Scaffold(
        appBar: AppBar(title: const Text('ShopBot')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              TextField(
                controller: _phoneController,
                decoration: const InputDecoration(labelText: 'Phone'),
              ),
              TextField(
                controller: _passwordController,
                decoration: const InputDecoration(labelText: 'Password'),
                obscureText: true,
              ),
              const SizedBox(height: 16),
              FilledButton(onPressed: _login, child: const Text('Login')),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('ShopBot'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadData),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(_reportToday, style: const TextStyle(fontSize: 16)),
            ),
          ),
          const SizedBox(height: 12),
          const Text('Low stock', style: TextStyle(fontWeight: FontWeight.bold)),
          ..._lowStock.map((p) => ListTile(
                title: Text(p['name'].toString()),
                trailing: Text('${p['stock_qty']} left'),
              )),
          const SizedBox(height: 12),
          const Text('Recent sales', style: TextStyle(fontWeight: FontWeight.bold)),
          ..._sales.take(10).map((s) => ListTile(
                title: Text(s['receipt_no'].toString()),
                trailing: Text('${s['total_amount']} TZS'),
              )),
        ],
      ),
    );
  }
}
