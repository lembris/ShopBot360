import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'services/api_service.dart';

void main() {
  runApp(const ShopBotApp());
}

class ShopBotApp extends StatelessWidget {
  const ShopBotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ShopBot',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0D9488)),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
