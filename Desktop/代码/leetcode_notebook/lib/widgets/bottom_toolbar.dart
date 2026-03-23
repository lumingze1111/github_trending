import 'dart:ui';

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

    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
          decoration: BoxDecoration(
            color: AppTheme.bgDeep.withValues(alpha: 0.85),
            border: const Border(top: BorderSide(color: AppTheme.borderLine, width: 1)),
          ),
          child: SafeArea(
            top: false,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _ToolbarButton(icon: Icons.arrow_back_ios_rounded, label: 'Prev', onTap: onPrevious),
                _ToolbarButton(icon: Icons.arrow_forward_ios_rounded, label: 'Next', onTap: onNext),
                _ToolbarButton(icon: Icons.shuffle_rounded, label: 'Random', onTap: onRandom),
                _ToolbarButton(icon: Icons.filter_list_rounded, label: 'Filter', onTap: onFilter,
                  color: hasActiveFilters ? AppTheme.blue : null),
                _ToolbarButton(
                  icon: isFavorited ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                  label: 'Favorite', onTap: onFavorite,
                  color: isFavorited ? AppTheme.green : null),
                _ToolbarButton(icon: Icons.bar_chart_rounded, label: 'Stats', onTap: onStatistics),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ToolbarButton extends StatefulWidget {
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
  State<_ToolbarButton> createState() => _ToolbarButtonState();
}

class _ToolbarButtonState extends State<_ToolbarButton> {
  bool _pressed = false;

  void _handleTap() {
    setState(() => _pressed = true);
    widget.onTap();
    Future.delayed(const Duration(milliseconds: 150), () {
      if (mounted) setState(() => _pressed = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final effectiveColor = widget.color ?? AppTheme.textSecondary;
    final isActive = widget.color != null;
    // 发光强度：激活状态或点击时增强
    final glowOpacity = _pressed ? 0.8 : (isActive ? 0.6 : 0.0);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: _handleTap,
        borderRadius: BorderRadius.circular(8),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: BoxDecoration(
            color: (isActive || _pressed)
                ? effectiveColor.withValues(alpha: _pressed ? 0.15 : 0.08)
                : null,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(
              widget.icon,
              size: 26,
              color: effectiveColor,
              shadows: glowOpacity > 0
                  ? [Shadow(color: effectiveColor.withValues(alpha: glowOpacity), blurRadius: 12)]
                  : null,
            ),
            const SizedBox(height: 3),
            Text(widget.label, style: AppTheme.monoStyle(size: 9, color: effectiveColor)),
          ]),
        ),
      ),
    );
  }
}
