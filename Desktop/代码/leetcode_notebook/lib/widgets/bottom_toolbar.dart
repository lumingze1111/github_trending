import 'package:flutter/material.dart';
import 'package:leetcode_notebook/theme/app_theme.dart';

/// Bottom toolbar with 6 action buttons
class BottomToolbar extends StatelessWidget {
  final VoidCallback onPrevious;
  final VoidCallback onNext;
  final VoidCallback onRandom;
  final VoidCallback onFilter;
  final VoidCallback onFavorite;
  final VoidCallback onStatistics;
  final bool isFavorited;
  final bool hasActiveFilters;

  const BottomToolbar({
    super.key,
    required this.onPrevious,
    required this.onNext,
    required this.onRandom,
    required this.onFilter,
    required this.onFavorite,
    required this.onStatistics,
    this.isFavorited = false,
    this.hasActiveFilters = false,
  });

  @override
  Widget build(BuildContext context) {

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
      decoration: const BoxDecoration(
        color: AppTheme.bgDeep,
        border: Border(top: BorderSide(color: AppTheme.borderLine, width: 1)),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _ToolbarButton(
              icon: Icons.arrow_back_ios_rounded,
              label: 'Prev',
              onTap: onPrevious,
            ),
            _ToolbarButton(
              icon: Icons.arrow_forward_ios_rounded,
              label: 'Next',
              onTap: onNext,
            ),
            _ToolbarButton(
              icon: Icons.shuffle_rounded,
              label: 'Random',
              onTap: onRandom,
            ),
            _ToolbarButton(
              icon: Icons.filter_list_rounded,
              label: 'Filter',
              onTap: onFilter,
              color: hasActiveFilters ? AppTheme.blue : null,
            ),
            _ToolbarButton(
              icon: isFavorited ? Icons.favorite_rounded : Icons.favorite_border_rounded,
              label: 'Favorite',
              onTap: onFavorite,
              color: isFavorited ? AppTheme.green : null,
            ),
            _ToolbarButton(
              icon: Icons.bar_chart_rounded,
              label: 'Stats',
              onTap: onStatistics,
            ),
          ],
        ),
      ),
    );
  }
}

class _ToolbarButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Color? color;

  const _ToolbarButton({
    required this.icon,
    required this.label,
    required this.onTap,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveColor = color ?? AppTheme.textSecondary;
    final isActive = color != null;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: isActive ? BoxDecoration(
            color: effectiveColor.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(8),
          ) : null,
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: 26, color: effectiveColor,
              shadows: isActive ? [Shadow(color: effectiveColor.withValues(alpha: 0.6), blurRadius: 8)] : null),
            const SizedBox(height: 3),
            Text(label, style: AppTheme.monoStyle(size: 9, color: effectiveColor)),
          ]),
        ),
      ),
    );
  }
}
