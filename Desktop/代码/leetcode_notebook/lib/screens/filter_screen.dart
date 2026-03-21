import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:leetcode_notebook/models/leetcode_problem.dart';
import 'package:leetcode_notebook/models/filter_options.dart';
import 'package:leetcode_notebook/services/filter_service.dart';

/// Filter screen shown as a bottom sheet
class FilterScreen extends StatefulWidget {
  final List<LeetCodeProblem>? problems;
  const FilterScreen({super.key, this.problems});

  @override
  State<FilterScreen> createState() => _FilterScreenState();
}

class _FilterScreenState extends State<FilterScreen> {
  late FilterOptions _localOptions;
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    final service = context.read<FilterService>();
    _localOptions = service.options;
    _searchController.text = _localOptions.searchQuery;
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final allTags = FilterService.getAllTags();

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      child: DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Handle
              Container(
                margin: const EdgeInsets.only(top: 12),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),

              // Header
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                child: Row(
                  children: [
                    Text('Filter Problems', style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                    const Spacer(),
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _localOptions = const FilterOptions();
                          _searchController.clear();
                        });
                      },
                      child: const Text('Reset'),
                    ),
                  ],
                ),
              ),

              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  children: [
                    // Search
                    TextField(
                      controller: _searchController,
                      decoration: InputDecoration(
                        hintText: 'Search by title or number...',
                        prefixIcon: const Icon(Icons.search),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      ),
                      onChanged: (value) {
                        setState(() {
                          _localOptions = _localOptions.copyWith(searchQuery: value);
                        });
                      },
                    ),
                    const SizedBox(height: 20),

                    // Difficulty
                    Text('Difficulty', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children: Difficulty.values.map((d) {
                        final selected = _localOptions.difficulties.contains(d);
                        return FilterChip(
                          label: Text(d.displayName),
                          selected: selected,
                          onSelected: (val) {
                            setState(() {
                              final newSet = Set<Difficulty>.from(_localOptions.difficulties);
                              if (val) { newSet.add(d); } else { newSet.remove(d); }
                              _localOptions = _localOptions.copyWith(difficulties: newSet);
                            });
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 20),

                    // Status
                    Text('Status', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children: [
                        _statusChip(FilterStatus.all, 'All'),
                        _statusChip(FilterStatus.completed, 'Completed'),
                        _statusChip(FilterStatus.uncompleted, 'Uncompleted'),
                        _statusChip(FilterStatus.favorited, 'Favorited'),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Tags
                    Text('Tags', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: allTags.map((tag) {
                        final selected = _localOptions.tags.contains(tag);
                        return FilterChip(
                          label: Text(tag, style: const TextStyle(fontSize: 12)),
                          selected: selected,
                          onSelected: (val) {
                            setState(() {
                              final newSet = Set<String>.from(_localOptions.tags);
                              if (val) { newSet.add(tag); } else { newSet.remove(tag); }
                              _localOptions = _localOptions.copyWith(tags: newSet);
                            });
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 24),
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
                    child: const Text('Apply Filters'),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    ),
    );
  }

  Widget _statusChip(FilterStatus status, String label) {
    final selected = _localOptions.status == status;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) {
        setState(() {
          _localOptions = _localOptions.copyWith(status: status);
        });
      },
    );
  }
}
