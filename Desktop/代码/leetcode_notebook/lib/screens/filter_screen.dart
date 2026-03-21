import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:leetcode_notebook/models/leetcode_problem.dart';
import 'package:leetcode_notebook/models/filter_options.dart';
import 'package:leetcode_notebook/services/filter_service.dart';
import 'package:leetcode_notebook/theme/app_theme.dart';

/// Filter screen shown as a bottom sheet
class FilterScreen extends StatefulWidget {
  final List<LeetCodeProblem> problems;
  const FilterScreen({super.key, required this.problems});

  @override
  State<FilterScreen> createState() => _FilterScreenState();
}

class _FilterScreenState extends State<FilterScreen> {
  late FilterOptions _localOptions;
  final _searchController = TextEditingController();
  String _searchQuery = '';
  List<LeetCodeProblem> _searchResults = [];

  @override
  void initState() {
    super.initState();
    _localOptions = context.read<FilterService>().options;
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged(String value) {
    setState(() {
      _searchQuery = value;
      if (value.isEmpty) {
        _searchResults = [];
      } else {
        final q = value.toLowerCase();
        _searchResults = widget.problems.where((p) =>
          p.title.toLowerCase().contains(q) ||
          p.titleCn.contains(q) ||
          p.leetcodeId.contains(q)
        ).take(10).toList();
      }
    });
  }

  Widget _buildSearchField() {
    return TextField(
      controller: _searchController,
      style: AppTheme.monoStyle(size: 13),
      decoration: InputDecoration(
        hintText: '搜索题目名称或编号...',
        hintStyle: AppTheme.monoStyle(size: 13, color: AppTheme.textSecondary),
        prefixIcon: Container(
          margin: const EdgeInsets.all(14),
          width: 6,
          height: 6,
          decoration: const BoxDecoration(
            color: AppTheme.blue,
            shape: BoxShape.circle,
          ),
        ),
        enabledBorder: const UnderlineInputBorder(
          borderSide: BorderSide(color: AppTheme.blue, width: 1),
        ),
        focusedBorder: const UnderlineInputBorder(
          borderSide: BorderSide(color: AppTheme.blue, width: 2),
        ),
        filled: false,
      ),
      onChanged: _onSearchChanged,
    );
  }

  Widget _buildHighlightedText(
    String text,
    String query,
    TextStyle style,
    TextStyle highlightStyle,
  ) {
    final lower = text.toLowerCase();
    final idx = lower.indexOf(query.toLowerCase());
    if (idx == -1) return Text(text, style: style);
    return RichText(
      text: TextSpan(children: [
        if (idx > 0) TextSpan(text: text.substring(0, idx), style: style),
        TextSpan(
          text: text.substring(idx, idx + query.length),
          style: highlightStyle,
        ),
        if (idx + query.length < text.length)
          TextSpan(text: text.substring(idx + query.length), style: style),
      ]),
    );
  }

  Widget _buildResultRow(LeetCodeProblem p) {
    final listIndex = widget.problems.indexOf(p);
    final diffColor = AppTheme.difficultyColor(p.difficulty.name);
    final normalStyle = AppTheme.monoStyle(size: 13);
    final highlightStyle = AppTheme.monoStyle(size: 13, color: AppTheme.blue)
        .copyWith(decoration: TextDecoration.underline);
    final normalStyleSm =
        AppTheme.monoStyle(size: 11, color: AppTheme.textSecondary);
    return InkWell(
      onTap: () => Navigator.pop(context, listIndex),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(children: [
          Container(width: 4, height: 40, color: diffColor),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHighlightedText(
                    p.titleCn, _searchQuery, normalStyle, highlightStyle),
                const SizedBox(height: 2),
                _buildHighlightedText(
                    p.title, _searchQuery, normalStyleSm, highlightStyle),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
            decoration: BoxDecoration(
              color: const Color(0x2600B4FF),
              border: Border.all(color: AppTheme.blue, width: 1),
            ),
            child: Text(
              '#${p.leetcodeId}',
              style: AppTheme.pixelStyle(size: 8, color: AppTheme.blue),
            ),
          ),
        ]),
      ),
    );
  }

  Widget _buildSearchResults({Key? key}) {
    if (_searchResults.isEmpty) {
      return Center(
        key: key,
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Text(
            'NO MATCH',
            style: AppTheme.pixelStyle(
                size: 12, color: AppTheme.textSecondary),
          ),
        ),
      );
    }
    return Column(
      key: key,
      children: _searchResults.map((p) => _buildResultRow(p)).toList(),
    );
  }

  String _buildActiveSummary() {
    final parts = <String>[];
    if (_localOptions.difficulties.isNotEmpty) {
      parts.add(_localOptions.difficulties.map((d) => d.name).join('/'));
    }
    if (_localOptions.status != FilterStatus.all) {
      parts.add(_localOptions.status.name);
    }
    if (_localOptions.tags.isNotEmpty) {
      parts.addAll(_localOptions.tags.take(2));
    }
    return 'Active: ${parts.join(' · ')}';
  }

  Widget _buildFilterSections({Key? key}) {
    final allTags = FilterService.getAllTags();
    return Column(
      key: key,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Difficulty section
        Text(
          'DIFFICULTY',
          style: AppTheme.pixelStyle(size: 10, color: AppTheme.textSecondary),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: Difficulty.values.map((d) {
            final selected = _localOptions.difficulties.contains(d);
            final diffColor = AppTheme.difficultyColor(d.name);
            return FilterChip(
              label: Text(
                d.displayName,
                style: AppTheme.monoStyle(size: 11),
              ),
              selected: selected,
              selectedColor: diffColor.withValues(alpha: 0.3),
              checkmarkColor: diffColor,
              side: BorderSide(color: diffColor),
              onSelected: (val) {
                setState(() {
                  final newSet = Set<Difficulty>.from(_localOptions.difficulties);
                  if (val) {
                    newSet.add(d);
                  } else {
                    newSet.remove(d);
                  }
                  _localOptions = _localOptions.copyWith(difficulties: newSet);
                });
              },
            );
          }).toList(),
        ),
        const SizedBox(height: 20),

        // Status section
        Text(
          'STATUS',
          style: AppTheme.pixelStyle(size: 10, color: AppTheme.textSecondary),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: [
            _statusChip(FilterStatus.all, 'All'),
            _statusChip(FilterStatus.completed, 'Completed'),
            _statusChip(FilterStatus.uncompleted, 'Uncompleted'),
            _statusChip(FilterStatus.favorited, 'Favorited'),
          ],
        ),
        const SizedBox(height: 20),

        // Tags section
        Text(
          'TAGS',
          style: AppTheme.pixelStyle(size: 10, color: AppTheme.textSecondary),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: allTags.map((tag) {
            final selected = _localOptions.tags.contains(tag);
            return FilterChip(
              label: Text(tag, style: AppTheme.monoStyle(size: 11)),
              selected: selected,
              selectedColor: AppTheme.blue.withValues(alpha: 0.2),
              checkmarkColor: AppTheme.blue,
              side: const BorderSide(color: AppTheme.blue, width: 1),
              onSelected: (val) {
                setState(() {
                  final newSet = Set<String>.from(_localOptions.tags);
                  if (val) {
                    newSet.add(tag);
                  } else {
                    newSet.remove(tag);
                  }
                  _localOptions = _localOptions.copyWith(tags: newSet);
                });
              },
            );
          }).toList(),
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _statusChip(FilterStatus status, String label) {
    final selected = _localOptions.status == status;
    return ChoiceChip(
      label: Text(label, style: AppTheme.monoStyle(size: 11)),
      selected: selected,
      selectedColor: AppTheme.blue.withValues(alpha: 0.3),
      side: const BorderSide(color: AppTheme.blue, width: 1),
      onSelected: (_) {
        setState(() {
          _localOptions = _localOptions.copyWith(status: status);
        });
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          color: AppTheme.bgSheet,
          child: Column(
            children: [
              // Drag handle
              Container(
                margin: const EdgeInsets.only(top: 12),
                width: 40,
                height: 4,
                color: AppTheme.gridLine,
              ),

              // Header
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                child: Row(
                  children: [
                    Text('FILTER', style: AppTheme.pixelStyle(size: 12)),
                    const Spacer(),
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _localOptions = const FilterOptions();
                          _searchController.clear();
                          _searchQuery = '';
                          _searchResults = [];
                        });
                      },
                      style: TextButton.styleFrom(
                        foregroundColor: AppTheme.textSecondary,
                        textStyle: AppTheme.pixelStyle(size: 9),
                      ),
                      child: const Text('RESET'),
                    ),
                  ],
                ),
              ),

              // Scrollable content
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  children: [
                    _buildSearchField(),
                    const SizedBox(height: 16),

                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 200),
                      child: _searchQuery.isEmpty
                          ? _buildFilterSections(key: const ValueKey('filters'))
                          : _buildSearchResults(key: const ValueKey('results')),
                    ),

                    // Active filters summary (only when search is empty and filters active)
                    if (_searchQuery.isEmpty && _localOptions.hasActiveFilters)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Text(
                          _buildActiveSummary(),
                          style: AppTheme.monoStyle(
                              size: 11, color: AppTheme.textSecondary),
                        ),
                      ),
                  ],
                ),
              ),

              // Apply button
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
                child: SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: () {
                      context.read<FilterService>().updateOptions(_localOptions);
                      Navigator.pop(context);
                    },
                    style: FilledButton.styleFrom(
                      backgroundColor: AppTheme.blue,
                      foregroundColor: AppTheme.bgDeep,
                      shape: const RoundedRectangleBorder(
                        borderRadius: BorderRadius.zero,
                      ),
                      textStyle: AppTheme.pixelStyle(size: 11),
                    ),
                    child: const Text('APPLY FILTERS'),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
