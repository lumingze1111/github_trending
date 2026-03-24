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

After a problem is first completed, it is scheduled for review at these intervals (days since last review/completion):

| Review session | Days since last event |
|---|---|
| 1st review | 1 day |
| 2nd review | 2 days |
| 3rd review | 4 days |
| 4th review | 7 days |
| 5th review | 15 days |
| 6th+ review | 30 days (permanent maintenance) |

The interval is looked up using `reviewCount` (0-indexed before the review happens):
- `reviewCount == 0` → next review in 1 day
- `reviewCount == 1` → next review in 2 days
- `reviewCount == 2` → next review in 4 days
- `reviewCount == 3` → next review in 7 days
- `reviewCount == 4` → next review in 15 days
- `reviewCount >= 5` → next review in 30 days

### Due-Today Determination

A completed problem is "due today" if:

```
daysSince(lastReviewDate ?? firstCompletedDate) >= intervals[reviewCount]
```

Where `daysSince` counts calendar days (not 24-hour periods) using midnight boundaries in local time.

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

This calls `ReviewService.getDueToday()` internally.

### Settings: Daily Limit

User's configured daily limit is stored in `SharedPreferences` under the key `daily_review_limit` (int, default 20, range 5–50).

A new `SettingsService` (or simple static helper) wraps the read/write.

---

## UI Layer

### Home Screen Banner

A `ReviewBanner` widget is inserted at the top of the card list in `CardLearningScreen`, above the existing card `PageView`.

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
- User can exit review mode early via AppBar back button; progress is preserved (reviewed cards don't reappear today)

### Settings Entry Point

In `StatisticsScreen`, add a new section card "每日复习设置" at the bottom containing:

- Label: "每日复习上限"
- Current value displayed (e.g. "20 题")
- A `Slider` (min: 5, max: 50, divisions: 9, default: 20)
- Changes are persisted immediately to `SharedPreferences`

---

## Component Boundaries

| Component | Responsibility | Depends On |
|---|---|---|
| `ReviewService` | Interval math, due-today logic | `UserProgress` model |
| `ProgressService` | Expose `getTodayReviewProblems()` | `ReviewService`, Hive |
| `SettingsService` | Read/write daily limit | `SharedPreferences` |
| `ReviewBanner` | Home screen banner widget | `ProgressService` |
| `CardLearningScreen` | Orchestrate review mode, pass filtered list | `ProgressService`, `SettingsService` |
| `StatisticsScreen` | Settings slider | `SettingsService` |

---

## Error Handling

- If `firstCompletedDate` is null for a completed problem (data inconsistency from older records), treat the problem as due immediately
- If `SharedPreferences` read fails, fall back silently to the default limit of 20
- Empty review queue is a valid state, handled by the banner's "completed" display

---

## Out of Scope

- Push notifications / local notifications for daily reminders
- Per-problem difficulty rating (SM-2 adaptive intervals)
- Review history log / streak tracking
- Cloud sync of review state
