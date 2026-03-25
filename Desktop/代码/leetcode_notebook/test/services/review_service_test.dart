import 'package:flutter_test/flutter_test.dart';
import 'package:leetcode_notebook/models/user_progress.dart';
import 'package:leetcode_notebook/services/review_service.dart';

// Helper to create a UserProgress without Hive (no save() calls needed)
UserProgress makeProgress({
  required int problemId,
  required bool isCompleted,
  int reviewCount = 0,
  DateTime? lastReviewDate,
}) {
  final p = UserProgress(
    problemId: problemId,
    isCompleted: isCompleted,
    reviewCount: reviewCount,
    lastReviewDate: lastReviewDate,
  );
  return p;
}

void main() {
  final service = ReviewService();

  group('isDueToday', () {
    test('not completed problem is never due', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: false,
        reviewCount: 1,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 10)),
      );
      expect(service.isDueToday(p), false);
    });

    test('reviewCount=1, lastReview 1 day ago: not due (needs 2 days)', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 1,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 1)),
      );
      expect(service.isDueToday(p), false);
    });

    test('reviewCount=1, lastReview 2 days ago: due', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 1,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 2)),
      );
      expect(service.isDueToday(p), true);
    });

    test('reviewCount=2, lastReview 3 days ago: not due (needs 4)', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 2,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 3)),
      );
      expect(service.isDueToday(p), false);
    });

    test('reviewCount=2, lastReview 4 days ago: due', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 2,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 4)),
      );
      expect(service.isDueToday(p), true);
    });

    test('reviewCount=3: due after 7 days', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 3,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 7)),
      );
      expect(service.isDueToday(p), true);
    });

    test('reviewCount=4: due after 15 days', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 4,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 15)),
      );
      expect(service.isDueToday(p), true);
    });

    test('reviewCount=5 (maintenance): due after 30 days', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 5,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 30)),
      );
      expect(service.isDueToday(p), true);
    });

    test('reviewCount=5 (maintenance): not due after 29 days', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 5,
        lastReviewDate: DateTime.now().subtract(const Duration(days: 29)),
      );
      expect(service.isDueToday(p), false);
    });

    test('null lastReviewDate with isCompleted=true: treated as due immediately', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 1,
        lastReviewDate: null,
      );
      expect(service.isDueToday(p), true);
    });

    test('just reviewed (0 days): not due', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 1,
        lastReviewDate: DateTime.now(),
      );
      expect(service.isDueToday(p), false);
    });

    test('reviewCount=0, isCompleted=true: due immediately (intervals[0]=0)', () {
      final p = makeProgress(
        problemId: 1,
        isCompleted: true,
        reviewCount: 0,
        lastReviewDate: DateTime.now(),
      );
      expect(service.isDueToday(p), true);
    });
  });

  group('getDueToday', () {
    test('returns empty list when no problems are due', () {
      final problems = [
        makeProgress(problemId: 1, isCompleted: true, reviewCount: 1,
            lastReviewDate: DateTime.now()),
      ];
      expect(service.getDueToday(problems), isEmpty);
    });

    test('returns problem IDs that are due', () {
      final problems = [
        makeProgress(problemId: 1, isCompleted: true, reviewCount: 1,
            lastReviewDate: DateTime.now().subtract(const Duration(days: 2))),
        makeProgress(problemId: 2, isCompleted: true, reviewCount: 1,
            lastReviewDate: DateTime.now()),
      ];
      expect(service.getDueToday(problems), [1]);
    });

    test('respects limit parameter', () {
      final problems = List.generate(
        25,
        (i) => makeProgress(
          problemId: i + 1,
          isCompleted: true,
          reviewCount: 1,
          lastReviewDate: DateTime.now().subtract(const Duration(days: 5)),
        ),
      );
      final result = service.getDueToday(problems, limit: 10);
      expect(result.length, 10);
    });

    test('sorts by most overdue first', () {
      final problems = [
        makeProgress(problemId: 1, isCompleted: true, reviewCount: 1,
            lastReviewDate: DateTime.now().subtract(const Duration(days: 3))), // 1 day overdue
        makeProgress(problemId: 2, isCompleted: true, reviewCount: 1,
            lastReviewDate: DateTime.now().subtract(const Duration(days: 10))), // 8 days overdue
        makeProgress(problemId: 3, isCompleted: true, reviewCount: 1,
            lastReviewDate: DateTime.now().subtract(const Duration(days: 2))), // 0 days overdue (just due)
      ];
      final result = service.getDueToday(problems);
      expect(result, [2, 1, 3]);
    });

    test('excludes uncompleted problems', () {
      final problems = [
        makeProgress(problemId: 1, isCompleted: false, reviewCount: 1,
            lastReviewDate: DateTime.now().subtract(const Duration(days: 10))),
      ];
      expect(service.getDueToday(problems), isEmpty);
    });
  });
}
