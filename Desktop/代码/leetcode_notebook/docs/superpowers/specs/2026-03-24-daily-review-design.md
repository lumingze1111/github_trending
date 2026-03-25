# Daily Review System — Design Spec

**Date:** 2026-03-24
**Feature:** Ebbinghaus spaced repetition daily review
**Status:** Approved

---

## Overview

Add a built-in daily review system to the LeetCode Notebook app. When the user has completed problems (tapped "mark as done"), the system schedules those problems for spaced repetition review using the Ebbinghaus forgetting curve intervals. Each day, the app surfaces a prioritized queue of due problems on the home screen so the user can review them without manual planning.

---

## Algorithm

### Ebbinghaus Intervals

**`reviewCount` at first completion:** The existing `FlipCardWidget` calls both `markCompleted()` and `incrementReview()` when the user taps "MARK AS DONE". This means `reviewCount` starts at **1** (not 0) after first completion, and `lastReviewDate` is always set. Do **not** change this existing behavior.

The `intervals` array is indexed by `reviewCount` value at the time of the due-today check. Since `reviewCount` starts at 1, index 0 is intentionally unused — the array is sized for direct indexing:

```dart
// intervals[reviewCount] = days to wait before next review
// index 0 is unused (reviewCount is always >= 1 for completed problems)
static const List<int> intervals = [0, 2, 4, 7, 15];
//                                   ^unused  ^ index 1..4 = reviews 1..4
static const int maintenanceInterval = 30; // reviewCount >= 5
```

The effective schedule (days since last review/completion):

| `reviewCount` after last event | Days until next review |
|---|---|
| 1 (just completed) | 2 days |
| 2 | 4 days |
| 3 | 7 days |
| 4 | 15 days |
| ≥ 5 | 30 days (permanent maintenance) |

`lastReviewDate` is used as the baseline (not `firstCompletedDate`) since it is always non-null for completed problems.

### Due-Today Determination

A completed problem is "due today" if:

```dart
int interval = reviewCount < intervals.length
    ? intervals[reviewCount]
    : maintenanceInterval;
int daysSince = DateTime.now().difference(lastReviewDate!).inDays;
bool isDue = daysSince >= interval;
```

`daysSince` uses `.inDays` (integer truncation of the Duration), consistent with calendar-day counting. `lastReviewDate` is always non-null for completed problems (set by `incrementReview` at first completion).

If `lastReviewDate` is null despite `isCompleted == true` (legacy data inconsistency), treat the problem as due immediately.

### Daily Queue

- Only **completed** problems (`isCompleted == true`) are eligible
- Problems are sorted by urgency: most overdue first (largest `daysSince - interval`)
- Queue is capped at the user's configured daily limit (default: **20 problems**)
- Once reviewed (user taps "✓ 已复习"), the problem is removed from today's queue

---

## Data Layer

### Existing Model — No Changes Required

`UserProgress` already has all necessary fields:
- `reviewCount` (int) — number of completed review sessions
- `lastReviewDate` (DateTime?) — timestamp of most recent review
- `firstCompletedDate` (DateTime?) — timestamp of initial completion
- `isCompleted` (bool) — eligibility gate

No Hive schema changes needed; no code generation required.

### New: `ReviewService`

A new stateless service class with a single clear responsibility: computing the review queue.

```dart
class ReviewService {
  static const List<int> intervals = [1, 2, 4, 7, 15];
  static const int maintenanceInterval = 30;

  /// Returns true if the problem is due for review today
  bool isDueToday(UserProgress progress);

  /// Returns sorted, capped list of problem IDs due today
  List<int> getDueToday(List<UserProgress> allProgress, {int limit = 20});
}
```

### `ProgressService` Addition

Add one method to `ProgressService` to expose the daily queue to the UI:

```dart
List<int> getTodayReviewProblems({int limit = 20});
```

This calls `ReviewService.getDueToday()` passing `_progressBox.values.toList()` and the limit parameter. `ProgressService` does **not** depend on `SettingsService` directly — the caller (`CardLearningScreen`) reads the limit from `SettingsService` and passes it in.

### Settings: `SettingsService`

A new async-initialized service wrapping `SharedPreferences`:

```dart
class SettingsService extends ChangeNotifier {
  static const _key = 'daily_review_limit';
  static const defaultLimit = 20;

  int _dailyLimit = defaultLimit;
  int get dailyLimit => _dailyLimit;

  /// Must be called once at app startup (in main.dart, after Hive init)
  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _dailyLimit = prefs.getInt(_key) ?? defaultLimit;
  }

  Future<void> setDailyLimit(int value) async {
    _dailyLimit = value;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_key, value);
  }
}
```

`SettingsService` is registered as a `ChangeNotifierProvider` in `main.dart` using the **instance pattern**: create the instance, call `await instance.init()`, then pass it to `ChangeNotifierProvider.value`:

```dart
// main.dart (after Hive init, before runApp)
final settingsService = SettingsService();
await settingsService.init();

runApp(MultiProvider(
  providers: [
    ChangeNotifierProvider(create: (_) => ProgressService()),
    ChangeNotifierProvider.value(value: settingsService),
    ...
  ],
  child: const MyApp(),
));
```

`shared_preferences` must be added to `pubspec.yaml` as a new dependency.

---

## UI Layer

### Home Screen Banner

`CardLearningScreen.build()` currently renders a `Stack` body with `Positioned.fill` background and a `PageView` as the single content layer. To insert the banner, the content layer changes from a bare `PageView` to a `Column` wrapping the banner + `PageView`:

```dart
// Body content layer (replaces the PageView directly):
Column(
  children: [
    ReviewBanner(),          // zero-height when hidden
    Expanded(child: PageView.builder(...)),
  ],
)
```

The `Positioned.fill` animated background remains unchanged. `ReviewBanner` is a `Consumer<ProgressService>` widget that reads the due-today count by calling `progressService.getTodayReviewProblems(limit: context.read<SettingsService>().dailyLimit).length`. It therefore depends on both `ProgressService` and `SettingsService` (both available via `Provider` at the widget tree level).

**States:**

| Condition | Banner appearance |
|---|---|
| No completed problems yet | Hidden (zero height) |
| Problems due today (N > 0) | "📅 今日复习  N 题待复习  [开始复习 →]" (accent color) |
| All due problems reviewed | "🎉 今日复习已完成" (green) |

The banner is a `Consumer<ProgressService>` so it reacts live to state changes.

### Review Mode

Triggered by tapping "开始复习" in the banner. Enters a filtered card flow:

- Uses same `FlipCardWidget` / `PageView` experience as normal learning
- AppBar title changes to "今日复习 {current}/{total}" (e.g. "今日复习 3/5")
- On the card back face, the "打卡" button is replaced by "✓ 已复习" button
- Tapping "✓ 已复习" calls `progressService.incrementReview(problemId)`, removes the card from the queue, and advances to next
- After the last card is reviewed, a completion dialog appears ("🎉 今日复习完成！"), then returns to home screen
- User can exit review mode early via AppBar back button; progress is preserved — reviewed cards don't reappear because `incrementReview()` updates `lastReviewDate` to now, making `daysSince` = 0 which is less than any interval

**Partial-review persistence across re-entry:** If the user reviews 3 of 5 due problems and exits, then re-enters review mode, the banner and review queue recompute live. The 3 reviewed problems will have `lastReviewDate = today`, so `daysSince = 0 < interval` → not due. Only the 2 unreviewed problems remain, so the banner shows "2 题待复习". This is the intended behavior.

### Settings Entry Point

In `StatisticsScreen`, add a new section card "每日复习设置" at the bottom containing:

- Label: "每日复习上限"
- Current value displayed (e.g. "20 题")
- A `Slider` (min: 5, max: 50, step size: 5, so `divisions: 9`, values: 5/10/15/…/50)
- Changes are persisted immediately to `SharedPreferences`

---

## Component Boundaries

| Component | Responsibility | Depends On |
|---|---|---|
| `ReviewService` | Interval math, due-today logic | `UserProgress` model |
| `ProgressService` | Expose `getTodayReviewProblems()` | `ReviewService`, Hive |
| `SettingsService` | Read/write daily limit (async init) | `SharedPreferences` |
| `ReviewBanner` | Home screen banner widget | `ProgressService`, `SettingsService` |
| `CardLearningScreen` | Orchestrate review mode, pass filtered list + limit | `ProgressService`, `SettingsService` |
| `StatisticsScreen` | Settings slider | `SettingsService` |

---

## Error Handling

- If `lastReviewDate` is null for a completed problem (legacy data inconsistency), treat the problem as due immediately
- If `SharedPreferences` read fails, fall back silently to the default limit of 20
- Empty review queue is a valid state, handled by the banner's "completed" display

---

## Out of Scope

- Push notifications / local notifications for daily reminders
- Per-problem difficulty rating (SM-2 adaptive intervals)
- Review history log / streak tracking
- Cloud sync of review state
