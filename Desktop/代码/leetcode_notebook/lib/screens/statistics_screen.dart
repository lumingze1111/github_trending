import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:provider/provider.dart';
import 'package:leetcode_notebook/models/leetcode_problem.dart';
import 'package:leetcode_notebook/data/problems_data.dart';
import 'package:leetcode_notebook/services/progress_service.dart';
import 'package:leetcode_notebook/services/settings_service.dart';

/// Statistics screen showing learning progress
class StatisticsScreen extends StatelessWidget {
  const StatisticsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Statistics'),
        centerTitle: true,
      ),
      body: Consumer<ProgressService>(
        builder: (context, service, _) {
          final total = hot100Problems.length;
          final completed = service.completedCount;
          final completionRate = total > 0 ? completed / total : 0.0;

          final easyTotal = hot100Problems.where((p) => p.difficulty == Difficulty.easy).length;
          final mediumTotal = hot100Problems.where((p) => p.difficulty == Difficulty.medium).length;
          final hardTotal = hot100Problems.where((p) => p.difficulty == Difficulty.hard).length;

          final completedIds = service.completedProblemIds.toSet();
          final easyDone = hot100Problems.where((p) => p.difficulty == Difficulty.easy && completedIds.contains(p.id)).length;
          final mediumDone = hot100Problems.where((p) => p.difficulty == Difficulty.medium && completedIds.contains(p.id)).length;
          final hardDone = hot100Problems.where((p) => p.difficulty == Difficulty.hard && completedIds.contains(p.id)).length;

          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              // Overall progress card
              _SectionCard(
                title: 'Overall Progress',
                child: Row(
                  children: [
                    SizedBox(
                      width: 120,
                      height: 120,
                      child: PieChart(
                        PieChartData(
                          sections: [
                            PieChartSectionData(
                              value: completed.toDouble(),
                              color: Colors.green,
                              title: '$completed',
                              radius: 45,
                              titleStyle: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                            ),
                            PieChartSectionData(
                              value: (total - completed).toDouble(),
                              color: Colors.grey.shade200,
                              title: '${total - completed}',
                              radius: 45,
                              titleStyle: const TextStyle(color: Colors.grey, fontWeight: FontWeight.bold),
                            ),
                          ],
                          centerSpaceRadius: 20,
                          sectionsSpace: 2,
                        ),
                      ),
                    ),
                    const SizedBox(width: 24),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('${(completionRate * 100).toStringAsFixed(1)}%',
                            style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
                          Text('$completed / $total problems completed',
                            style: TextStyle(color: Colors.grey.shade600)),
                          const SizedBox(height: 8),
                          LinearProgressIndicator(
                            value: completionRate,
                            backgroundColor: Colors.grey.shade200,
                            color: Colors.green,
                            minHeight: 8,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Difficulty breakdown
              _SectionCard(
                title: 'By Difficulty',
                child: Column(
                  children: [
                    _DifficultyRow(label: 'Easy', done: easyDone, total: easyTotal, color: const Color(0xFF00B8A3)),
                    const SizedBox(height: 12),
                    _DifficultyRow(label: 'Medium', done: mediumDone, total: mediumTotal, color: const Color(0xFFFFC01E)),
                    const SizedBox(height: 12),
                    _DifficultyRow(label: 'Hard', done: hardDone, total: hardTotal, color: const Color(0xFFFF375F)),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Summary stats
              _SectionCard(
                title: 'Summary',
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _StatItem(label: 'Completed', value: '$completed', icon: Icons.check_circle, color: Colors.green),
                    _StatItem(label: 'Favorited', value: '${service.favoritedCount}', icon: Icons.favorite, color: Colors.red),
                    _StatItem(label: 'Remaining', value: '${total - completed}', icon: Icons.pending, color: Colors.orange),
                  ],
                ),
              ),
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
            ],
          );
        },
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final Widget child;

  const _SectionCard({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            child,
          ],
        ),
      ),
    );
  }
}

class _DifficultyRow extends StatelessWidget {
  final String label;
  final int done;
  final int total;
  final Color color;

  const _DifficultyRow({required this.label, required this.done, required this.total, required this.color});

  @override
  Widget build(BuildContext context) {
    final rate = total > 0 ? done / total : 0.0;
    return Row(
      children: [
        SizedBox(width: 60, child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w600))),
        Expanded(
          child: LinearProgressIndicator(
            value: rate,
            backgroundColor: color.withValues(alpha: 0.15),
            color: color,
            minHeight: 8,
            borderRadius: BorderRadius.circular(4),
          ),
        ),
        const SizedBox(width: 12),
        Text('$done/$total', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
      ],
    );
  }
}

class _StatItem extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _StatItem({required this.label, required this.value, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        Text(label, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
      ],
    );
  }
}
