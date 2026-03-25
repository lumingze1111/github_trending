import 'package:flutter/foundation.dart';
import 'package:hive/hive.dart';
import 'package:leetcode_notebook/models/user_progress.dart';
import 'package:leetcode_notebook/services/review_service.dart';

/// Service for managing user progress data
class ProgressService extends ChangeNotifier {
  late Box<UserProgress> _progressBox;

  ProgressService() {
    _progressBox = Hive.box<UserProgress>('user_progress');
  }

  /// Get progress for a specific problem
  UserProgress? getProgress(int problemId) {
    return _progressBox.get(problemId);
  }

  /// Get or create progress for a problem
  UserProgress getOrCreateProgress(int problemId) {
    var progress = _progressBox.get(problemId);
    if (progress == null) {
      progress = UserProgress(problemId: problemId);
      _progressBox.put(problemId, progress);
    }
    return progress;
  }

  /// Mark problem as uncompleted
  void unmarkCompleted(int problemId) {
    final progress = getOrCreateProgress(problemId);
    progress.unmarkCompleted();
    notifyListeners();
  }

  /// Mark problem as completed
  void markCompleted(int problemId) {
    final progress = getOrCreateProgress(problemId);
    progress.markCompleted();
    notifyListeners();
  }

  /// Toggle favorite status
  void toggleFavorite(int problemId) {
    final progress = getOrCreateProgress(problemId);
    progress.toggleFavorite();
    notifyListeners();
  }

  /// Increment review count
  void incrementReview(int problemId) {
    final progress = getOrCreateProgress(problemId);
    progress.incrementReview();
    notifyListeners();
  }

  /// Check if problem is completed
  bool isCompleted(int problemId) {
    final progress = _progressBox.get(problemId);
    return progress?.isCompleted ?? false;
  }

  /// Check if problem is favorited
  bool isFavorited(int problemId) {
    final progress = _progressBox.get(problemId);
    return progress?.isFavorited ?? false;
  }

  /// Get total completed count
  int get completedCount {
    return _progressBox.values.where((p) => p.isCompleted).length;
  }

  /// Get total favorited count
  int get favoritedCount {
    return _progressBox.values.where((p) => p.isFavorited).length;
  }

  /// Get all completed problem IDs
  List<int> get completedProblemIds {
    return _progressBox.values
        .where((p) => p.isCompleted)
        .map((p) => p.problemId)
        .toList();
  }

  /// Get all favorited problem IDs
  List<int> get favoritedProblemIds {
    return _progressBox.values
        .where((p) => p.isFavorited)
        .map((p) => p.problemId)
        .toList();
  }

  /// Get problem IDs due for review today, sorted by urgency, capped at [limit].
  List<int> getTodayReviewProblems({int limit = 20}) {
    final reviewService = ReviewService();
    return reviewService.getDueToday(_progressBox.values.toList(), limit: limit);
  }
}
