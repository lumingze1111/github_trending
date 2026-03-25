import 'package:leetcode_notebook/models/user_progress.dart';

/// Stateless service for Ebbinghaus spaced repetition interval logic.
///
/// reviewCount is always >= 1 for completed problems (incremented at first completion).
/// intervals[reviewCount] = days to wait before the next review.
/// Index 0 is intentionally unused.
class ReviewService {
  static const List<int> intervals = [0, 2, 4, 7, 15];
  static const int maintenanceInterval = 30;

  /// Returns true if the problem is due for review today.
  bool isDueToday(UserProgress progress) {
    if (!progress.isCompleted) return false;
    if (progress.lastReviewDate == null) return true; // legacy data: treat as due

    final interval = progress.reviewCount < intervals.length
        ? intervals[progress.reviewCount]
        : maintenanceInterval;
    final daysSince = DateTime.now().difference(progress.lastReviewDate!).inDays;
    return daysSince >= interval;
  }

  /// Returns sorted, capped list of problem IDs due today.
  ///
  /// Sorted by most overdue first (largest daysSince - interval).
  /// Capped at [limit].
  List<int> getDueToday(List<UserProgress> allProgress, {int limit = 20}) {
    final due = allProgress.where(isDueToday).toList();

    due.sort((a, b) {
      final overdueA = _overdueBy(a);
      final overdueB = _overdueBy(b);
      return overdueB.compareTo(overdueA); // descending: most overdue first
    });

    return due.take(limit).map((p) => p.problemId).toList();
  }

  int _overdueBy(UserProgress progress) {
    if (progress.lastReviewDate == null) return 999999;
    final interval = progress.reviewCount < intervals.length
        ? intervals[progress.reviewCount]
        : maintenanceInterval;
    return DateTime.now().difference(progress.lastReviewDate!).inDays - interval;
  }
}
