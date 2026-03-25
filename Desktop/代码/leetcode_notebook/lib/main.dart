import 'package:leetcode_notebook/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:provider/provider.dart';
import 'package:leetcode_notebook/models/user_progress.dart';
import 'package:leetcode_notebook/services/progress_service.dart';
import 'package:leetcode_notebook/services/filter_service.dart';
import 'package:leetcode_notebook/services/settings_service.dart';
import 'package:leetcode_notebook/screens/card_learning_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Hive
  await Hive.initFlutter();

  // Register Hive adapters
  Hive.registerAdapter(UserProgressAdapter());

  // Open Hive boxes
  await Hive.openBox<UserProgress>('user_progress');

  // Initialize settings (reads from SharedPreferences)
  final settingsService = SettingsService();
  await settingsService.init();

  runApp(LeetCodeApp(settingsService: settingsService));
}

class LeetCodeApp extends StatelessWidget {
  final SettingsService settingsService;

  const LeetCodeApp({super.key, required this.settingsService});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ProgressService()),
        ChangeNotifierProvider(create: (_) => FilterService()),
        ChangeNotifierProvider.value(value: settingsService),
      ],
      child: MaterialApp(
        title: 'LeetCode Hot 100',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.theme,
        darkTheme: AppTheme.theme,
        themeMode: ThemeMode.dark,
        home: const CardLearningScreen(),
      ),
    );
  }
}
