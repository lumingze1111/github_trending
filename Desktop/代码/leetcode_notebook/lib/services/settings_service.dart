import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Service for persisting user settings via SharedPreferences.
class SettingsService extends ChangeNotifier {
  static const String _key = 'daily_review_limit';
  static const int defaultLimit = 20;

  int _dailyLimit = defaultLimit;
  int get dailyLimit => _dailyLimit;

  /// Load settings from SharedPreferences.
  /// Must be called once at app startup before runApp.
  Future<void> init() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _dailyLimit = prefs.getInt(_key) ?? defaultLimit;
    } catch (_) {
      // Fall back to default silently
    }
  }

  /// Update the daily review limit and persist it.
  Future<void> setDailyLimit(int value) async {
    _dailyLimit = value;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_key, value);
    } catch (_) {
      // Persist failure is non-fatal; in-memory value is updated
    }
  }
}
