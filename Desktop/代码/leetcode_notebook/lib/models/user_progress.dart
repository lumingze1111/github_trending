import 'package:hive/hive.dart';

part 'user_progress.g.dart';

/// Model for tracking user progress on each problem
@HiveType(typeId: 0)
class UserProgress extends HiveObject {
  @HiveField(0)
  final int problemId;

  @HiveField(1)
  bool isCompleted;

  @HiveField(2)
  bool isFavorited;

  @HiveField(3)
  int reviewCount;

  @HiveField(4)
  DateTime? lastReviewDate;

  @HiveField(5)
  DateTime? firstCompletedDate;

  UserProgress({
    required this.problemId,
    this.isCompleted = false,
    this.isFavorited = false,
    this.reviewCount = 0,
    this.lastReviewDate,
    this.firstCompletedDate,
  });

  /// Mark problem as completed
  void markCompleted() {
    isCompleted = true;
    firstCompletedDate ??= DateTime.now();
    save();
  }

  /// Mark problem as uncompleted
  void unmarkCompleted() {
    isCompleted = false;
    save();
  }

  /// Toggle favorite status
  void toggleFavorite() {
    isFavorited = !isFavorited;
    save();
  }

  /// Increment review count
  void incrementReview() {
    reviewCount++;
    lastReviewDate = DateTime.now();
    save();
  }
}
