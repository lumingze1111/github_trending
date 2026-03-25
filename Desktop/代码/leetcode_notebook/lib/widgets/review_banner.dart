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
