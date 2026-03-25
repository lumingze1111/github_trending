# Daily Review System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Ebbinghaus spaced repetition daily review system that surfaces due problems on the home screen each day.

**Architecture:** A new stateless `ReviewService` computes which completed problems are due for review using fixed intervals `[0, 2, 4, 7, 15]` days (index=reviewCount). A new `SettingsService` persists the user's daily limit via SharedPreferences. `CardLearningScreen` gains a `ReviewBanner` at the top and a review mode that replaces the "打卡" button with "✓ 已复习".

**Tech Stack:** Flutter, Dart, Hive (existing), SharedPreferences (new), Provider (existing)

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `pubspec.yaml` | Modify | Add `shared_preferences` dependency |
| `lib/services/review_service.dart` | **Create** | Ebbinghaus interval math + due-today logic |
| `lib/services/settings_service.dart` | **Create** | SharedPreferences wrapper for daily limit |
| `lib/services/progress_service.dart` | Modify | Add `getTodayReviewProblems()` method |
| `lib/main.dart` | Modify | Init `SettingsService`, add to MultiProvider |
| `lib/widgets/review_banner.dart` | **Create** | Home screen banner widget |
| `lib/screens/card_learning_screen.dart` | Modify | Insert banner, add review mode state |
| `lib/screens/statistics_screen.dart` | Modify | Add daily limit settings card |
| `test/services/review_service_test.dart` | **Create** | Unit tests for ReviewService |

---

## Task 1: Add `shared_preferences` dependency

**Files:**
- Modify: `pubspec.yaml`

- [ ] **Step 1: Add the dependency**

In `pubspec.yaml`, add under the `dependencies:` section after `intl`:

```yaml
  shared_preferences: ^2.3.0    # Persist user settings
```

- [ ] **Step 2: Install the package**

```bash
flutter pub get
```

Expected output: lines ending with `Got dependencies!`

- [ ] **Step 3: Commit**

```bash
git add pubspec.yaml pubspec.lock
git commit -m "chore: add shared_preferences dependency"
```

---

## Task 2: Implement `ReviewService` with tests

**Files:**
- Create: `lib/services/review_service.dart`
- Create: `test/services/review_service_test.dart`

- [ ] **Step 1: Write failing tests first**

Create `test/services/review_service_test.dart`:

```dart
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/lumingze/Desktop/代码/leetcode_notebook
flutter test test/services/review_service_test.dart
```

Expected: FAIL with "Target of URI doesn't exist: review_service.dart" or similar

- [ ] **Step 3: Implement `ReviewService`**

Create `lib/services/review_service.dart`:

```dart
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
flutter test test/services/review_service_test.dart
```

Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add lib/services/review_service.dart test/services/review_service_test.dart
git commit -m "feat: add ReviewService with Ebbinghaus interval logic"
```

---

## Task 3: Implement `SettingsService`

**Files:**
- Create: `lib/services/settings_service.dart`

No unit tests for this task — it's a thin wrapper around SharedPreferences; testing would require mocking the plugin, which adds more complexity than value.

- [ ] **Step 1: Create `SettingsService`**

Create `lib/services/settings_service.dart`:

```dart
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
```

- [ ] **Step 2: Verify it compiles**

```bash
flutter analyze lib/services/settings_service.dart
```

Expected: No errors (info-level warnings about unrelated files are okay)

- [ ] **Step 3: Commit**

```bash
git add lib/services/settings_service.dart
git commit -m "feat: add SettingsService for daily review limit"
```

---

## Task 4: Wire up `ProgressService` and `main.dart`

**Files:**
- Modify: `lib/services/progress_service.dart`
- Modify: `lib/main.dart`

- [ ] **Step 1: Add `getTodayReviewProblems` to `ProgressService`**

Open `lib/services/progress_service.dart`. At the bottom of the class, before the closing `}`, add:

```dart
  /// Get problem IDs due for review today, sorted by urgency, capped at [limit].
  List<int> getTodayReviewProblems({int limit = 20}) {
    final reviewService = ReviewService();
    return reviewService.getDueToday(_progressBox.values.toList(), limit: limit);
  }
```

Also add the import at the top of the file:

```dart
import 'package:leetcode_notebook/services/review_service.dart';
```

- [ ] **Step 2: Update `main.dart` to init and provide `SettingsService`**

Replace the entire `lib/main.dart` with:

```dart
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
```

- [ ] **Step 3: Verify compilation**

```bash
flutter analyze lib/
```

Expected: No new errors

- [ ] **Step 4: Commit**

```bash
git add lib/services/progress_service.dart lib/main.dart
git commit -m "feat: wire SettingsService and getTodayReviewProblems into app"
```

---

## Task 5: Add `ReviewBanner` widget

**Files:**
- Create: `lib/widgets/review_banner.dart`

- [ ] **Step 1: Create `ReviewBanner`**

Create `lib/widgets/review_banner.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:leetcode_notebook/services/progress_service.dart';
import 'package:leetcode_notebook/services/settings_service.dart';
import 'package:leetcode_notebook/theme/app_theme.dart';

/// Home screen banner showing today's review status.
/// Hidden if no completed problems exist.
class ReviewBanner extends StatelessWidget {
  /// Called when user taps "开始复习". Receives the list of due problem IDs.
  final void Function(List<int> dueProblemIds) onStartReview;

  const ReviewBanner({super.key, required this.onStartReview});

  @override
  Widget build(BuildContext context) {
    return Consumer2<ProgressService, SettingsService>(
      builder: (context, progress, settings, _) {
        final dueIds = progress.getTodayReviewProblems(limit: settings.dailyLimit);
        final hasCompleted = progress.completedCount > 0;

        if (!hasCompleted) return const SizedBox.shrink();

        if (dueIds.isEmpty) {
          // All reviews done for today
          return _BannerTile(
            color: AppTheme.green,
            child: Text(
              '🎉 今日复习已完成',
              style: AppTheme.monoStyle(size: 12, color: AppTheme.bgDeep, weight: FontWeight.bold),
            ),
          );
        }

        // Reviews pending
        return GestureDetector(
          onTap: () => onStartReview(dueIds),
          child: _BannerTile(
            color: AppTheme.blue,
            child: Row(
              children: [
                Text(
                  '📅 今日复习  ${dueIds.length} 题待复习',
                  style: AppTheme.monoStyle(size: 12, color: AppTheme.bgDeep, weight: FontWeight.bold),
                ),
                const Spacer(),
                Text(
                  '开始复习 →',
                  style: AppTheme.monoStyle(size: 11, color: AppTheme.bgDeep),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _BannerTile extends StatelessWidget {
  final Color color;
  final Widget child;

  const _BannerTile({required this.color, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: color,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: child,
    );
  }
}
```

- [ ] **Step 2: Verify compilation**

```bash
flutter analyze lib/widgets/review_banner.dart
```

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add lib/widgets/review_banner.dart
git commit -m "feat: add ReviewBanner widget"
```

---

## Task 6: Integrate review mode into `CardLearningScreen`

**Files:**
- Modify: `lib/screens/card_learning_screen.dart`
- Modify: `lib/widgets/flip_card_widget.dart`

This is the most complex task. Review mode adds a boolean `_isReviewMode` and a `List<int> _reviewProblemIds` to the screen state. When active, the AppBar title changes, problems are filtered to the due list, and a "✓ 已复习" button replaces "MARK AS DONE" on card backs.

- [ ] **Step 1: Add review mode state and methods to `_CardLearningScreenState`**

In `lib/screens/card_learning_screen.dart`:

1. Add imports at the top:
```dart
import 'package:leetcode_notebook/widgets/review_banner.dart';
import 'package:leetcode_notebook/services/settings_service.dart';
```

2. Add state variables inside `_CardLearningScreenState` (after `List<LeetCodeProblem> _problems = [];`):
```dart
  bool _isReviewMode = false;
  List<int> _reviewProblemIds = [];
  int _reviewedCount = 0;
```

3. Add the `_enterReviewMode` method (after `_refreshProblems`):
```dart
  void _enterReviewMode(List<int> dueIds) {
    final allProblems = context.read<FilterService>().getFilteredProblems();
    // Preserve the order from ReviewService (most overdue first)
    final reviewProblems = dueIds
        .map((id) => allProblems.firstWhere((p) => p.id == id, orElse: () => null as dynamic))
        .whereType<LeetCodeProblem>()
        .toList();

    if (reviewProblems.isEmpty) return;

    setState(() {
      _isReviewMode = true;
      _reviewProblemIds = dueIds;
      _reviewedCount = 0;
      _problems = reviewProblems;
      _currentIndex = 0;
    });
    _pageController.jumpToPage(0);
  }
```

4. Add `_exitReviewMode` method:
```dart
  void _exitReviewMode() {
    setState(() {
      _isReviewMode = false;
      _reviewProblemIds = [];
      _reviewedCount = 0;
    });
    _refreshProblems();
    _pageController.jumpToPage(0);
  }
```

5. Add `_onReviewDone` method (called when user taps "✓ 已复习"):
```dart
  void _onReviewDone(int problemId) {
    final service = context.read<ProgressService>();
    service.incrementReview(problemId);

    final newCount = _reviewedCount + 1;
    if (newCount >= _problems.length) {
      // All reviewed — show completion dialog
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (_) => AlertDialog(
          backgroundColor: AppTheme.bgCard,
          title: Text('🎉 今日复习完成！',
              style: AppTheme.monoStyle(size: 14, weight: FontWeight.bold)),
          content: Text('已完成今日所有复习题目。',
              style: AppTheme.monoStyle(size: 12, color: AppTheme.textSecondary)),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                _exitReviewMode();
              },
              child: Text('返回', style: AppTheme.monoStyle(size: 12, color: AppTheme.blue)),
            ),
          ],
        ),
      );
    } else {
      setState(() => _reviewedCount = newCount);
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }
```

- [ ] **Step 2: Update the AppBar title to show review mode progress**

In `build()`, find the `appBar:` section. Replace the title `Consumer<FilterService>` block with:

```dart
        title: _isReviewMode
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('今日复习',
                      style: AppTheme.pixelStyle(size: 11, color: AppTheme.green).copyWith(
                        shadows: [Shadow(color: AppTheme.green.withValues(alpha: 0.6), blurRadius: 8)],
                      )),
                  Text(
                    '${_reviewedCount + 1} / ${_problems.length}',
                    style: AppTheme.pixelNumberStyle(size: 13, color: AppTheme.green),
                  ),
                ],
              )
            : Consumer<FilterService>(
                builder: (context, filterService, _) {
                  final filtered = filterService.hasActiveFilters;
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'LeetCode Hot 100',
                        style: AppTheme.pixelStyle(size: 11, color: AppTheme.blue).copyWith(
                          shadows: [Shadow(color: AppTheme.blue.withValues(alpha: 0.6), blurRadius: 8)],
                        ),
                      ),
                      if (_problems.isNotEmpty)
                        Text(
                          filtered
                              ? '${_currentIndex + 1} / ${_problems.length} (filtered)'
                              : '${_currentIndex + 1} / ${_problems.length}',
                          style: AppTheme.pixelNumberStyle(size: 13, color: AppTheme.green),
                        ),
                    ],
                  );
                },
              ),
```

Also add a leading back button when in review mode. In the `AppBar`, add:

```dart
        leading: _isReviewMode
            ? IconButton(
                icon: const Icon(Icons.arrow_back, color: AppTheme.textSecondary),
                onPressed: _exitReviewMode,
              )
            : null,
```

- [ ] **Step 3: Update the body Stack to include ReviewBanner**

In `build()`, find the `body: Stack(...)` section. The current content layer is:

```dart
          _problems.isEmpty
              ? _buildEmptyState()
              : PageView.builder(...)
```

Replace it with a `Column` that adds the banner above the PageView, but only in normal mode:

```dart
          _problems.isEmpty
              ? _buildEmptyState()
              : Column(
                  children: [
                    if (!_isReviewMode)
                      ReviewBanner(onStartReview: _enterReviewMode),
                    Expanded(
                      child: PageView.builder(
                        controller: _pageController,
                        itemCount: _problems.length,
                        onPageChanged: (index) {
                          setState(() => _currentIndex = index);
                        },
                        itemBuilder: (context, index) {
                          return FlipCardWidget(
                            key: ValueKey(_problems[index].id),
                            problem: _problems[index],
                            isReviewMode: _isReviewMode,
                            onReviewDone: _isReviewMode ? _onReviewDone : null,
                          );
                        },
                      ),
                    ),
                  ],
                ),
```

- [ ] **Step 4: Update `FlipCardWidget` to support review mode**

Open `lib/widgets/flip_card_widget.dart`.

1. Add parameters to `FlipCardWidget`:
```dart
class FlipCardWidget extends StatefulWidget {
  final LeetCodeProblem problem;
  final bool isReviewMode;
  final void Function(int problemId)? onReviewDone;

  const FlipCardWidget({
    super.key,
    required this.problem,
    this.isReviewMode = false,
    this.onReviewDone,
  });
  // ...
}
```

2. In `_buildBack()`, replace the "Mark Done button" section (the `Consumer<ProgressService>` block at the bottom) with:

```dart
            // Action button
            const SizedBox(height: 8),
            widget.isReviewMode
                ? GestureDetector(
                    onTap: () => widget.onReviewDone?.call(widget.problem.id),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      decoration: BoxDecoration(
                        color: AppTheme.green,
                        border: Border.all(color: AppTheme.green, width: 2),
                      ),
                      child: Center(child: Text(
                        '✓ 已复习',
                        style: AppTheme.pixelStyle(size: 10, color: AppTheme.bgDeep),
                      )),
                    ),
                  )
                : Consumer<ProgressService>(builder: (context, service, _) {
                    final done = service.isCompleted(widget.problem.id);
                    return GestureDetector(
                      onTap: () {
                        if (done) {
                          service.unmarkCompleted(widget.problem.id);
                        } else {
                          service.markCompleted(widget.problem.id);
                          service.incrementReview(widget.problem.id);
                        }
                      },
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: done ? AppTheme.green : Colors.transparent,
                          border: Border.all(color: done ? AppTheme.green : AppTheme.blue, width: 2),
                        ),
                        child: Center(child: Text(
                          done ? '✓ COMPLETED' : 'MARK AS DONE',
                          style: AppTheme.pixelStyle(size: 10,
                            color: done ? AppTheme.bgDeep : AppTheme.blue),
                        )),
                      ),
                    );
                  }),
```

- [ ] **Step 5: Verify compilation**

```bash
flutter analyze lib/
```

Expected: No new errors (pre-existing info warnings are OK)

- [ ] **Step 6: Commit**

```bash
git add lib/screens/card_learning_screen.dart lib/widgets/flip_card_widget.dart lib/widgets/review_banner.dart
git commit -m "feat: add review mode to CardLearningScreen and FlipCardWidget"
```

---

## Task 7: Add daily limit settings to `StatisticsScreen`

**Files:**
- Modify: `lib/screens/statistics_screen.dart`

- [ ] **Step 1: Add imports to `statistics_screen.dart`**

Add at the top of `lib/screens/statistics_screen.dart`:

```dart
import 'package:leetcode_notebook/services/settings_service.dart';
```

- [ ] **Step 2: Add the settings card at the bottom of the ListView**

In `StatisticsScreen.build()`, find the `ListView` children list. After the last `SizedBox(height: 16)` and `_SectionCard` (the "Summary" card), add:

```dart
              const SizedBox(height: 16),
              Consumer<SettingsService>(
                builder: (context, settings, _) {
                  return _SectionCard(
                    title: '每日复习设置',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('每日复习上限'),
                            Text('${settings.dailyLimit} 题',
                                style: const TextStyle(fontWeight: FontWeight.bold)),
                          ],
                        ),
                        Slider(
                          value: settings.dailyLimit.toDouble(),
                          min: 5,
                          max: 50,
                          divisions: 9,
                          label: '${settings.dailyLimit} 题',
                          onChanged: (value) {
                            settings.setDailyLimit(value.toInt());
                          },
                        ),
                        Text(
                          '每次递增 5 题，范围 5–50 题',
                          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                  );
                },
              ),
```

- [ ] **Step 3: Verify compilation**

```bash
flutter analyze lib/screens/statistics_screen.dart
```

Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add lib/screens/statistics_screen.dart
git commit -m "feat: add daily review limit settings to StatisticsScreen"
```

---

## Task 8: Run all tests and verify

- [ ] **Step 1: Run unit tests**

```bash
flutter test
```

Expected: All tests pass

- [ ] **Step 2: Run analyze**

```bash
flutter analyze lib/
```

Expected: No new errors beyond pre-existing info warnings

- [ ] **Step 3: Manual smoke test checklist**

Run `flutter run` and verify:

- [ ] Home screen: no banner when 0 problems completed
- [ ] Complete 1 problem → banner appears "1 题待复习" (may need to wait until tomorrow, or temporarily set `lastReviewDate` to 2 days ago in debug)
- [ ] Tap "开始复习" → enters review mode, AppBar shows "今日复习 1/1"
- [ ] Flip card → back shows "✓ 已复习" button (not "MARK AS DONE")
- [ ] Tap "✓ 已复习" → completion dialog appears → dismiss → returns to home, banner shows "🎉 今日复习已完成"
- [ ] Open Statistics → "每日复习设置" card visible, Slider works, value updates live
- [ ] Tap back during review → returns to normal mode, banner recalculates correctly

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "test: verify daily review system passes all checks"
```
