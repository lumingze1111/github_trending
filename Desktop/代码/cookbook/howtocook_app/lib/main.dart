import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const HowToCookApp());
}

class HowToCookApp extends StatelessWidget {
  const HowToCookApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '程序员做饭指南',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.orange),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
