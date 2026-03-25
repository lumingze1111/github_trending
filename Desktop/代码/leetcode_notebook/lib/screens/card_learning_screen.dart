import 'dart:math';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:leetcode_notebook/models/leetcode_problem.dart';
import 'package:leetcode_notebook/services/progress_service.dart';
import 'package:leetcode_notebook/services/filter_service.dart';
import 'package:leetcode_notebook/widgets/flip_card_widget.dart';
import 'package:leetcode_notebook/widgets/bottom_toolbar.dart';
import 'package:leetcode_notebook/widgets/review_banner.dart';
import 'package:leetcode_notebook/screens/statistics_screen.dart';
import 'package:leetcode_notebook/screens/filter_screen.dart';
import 'package:leetcode_notebook/theme/app_theme.dart';
import 'package:leetcode_notebook/data/problems_data.dart';

/// Main learning screen with flip cards and navigation
class CardLearningScreen extends StatefulWidget {
  const CardLearningScreen({super.key});

  @override
  State<CardLearningScreen> createState() => _CardLearningScreenState();
}

class _CardLearningScreenState extends State<CardLearningScreen>
    with TickerProviderStateMixin {
  final PageController _pageController = PageController();
  int _currentIndex = 0;
  List<LeetCodeProblem> _problems = [];
  bool _isReviewMode = false;
  int _reviewedCount = 0;
  late AnimationController _bgController;
  late Animation<Alignment> _light1;
  late Animation<Alignment> _light2;

  @override
  void initState() {
    super.initState();
    _bgController = AnimationController(
      duration: const Duration(seconds: 20),
      vsync: this,
    )..repeat(reverse: true);

    _light1 = AlignmentTween(
      begin: const Alignment(-0.5, -0.8),
      end: const Alignment(0.5, 0.3),
    ).animate(CurvedAnimation(parent: _bgController, curve: Curves.easeInOutSine));

    _light2 = AlignmentTween(
      begin: const Alignment(0.6, -0.5),
      end: const Alignment(-0.4, 0.6),
    ).animate(CurvedAnimation(parent: _bgController, curve: Curves.easeInOutSine));

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _refreshProblems();
    });
  }

  @override
  void dispose() {
    _pageController.dispose();
    _bgController.dispose();
    super.dispose();
  }

  void _refreshProblems() {
    final filterService = context.read<FilterService>();
    final progressService = context.read<ProgressService>();
    filterService.setProgressService(progressService);
    setState(() {
      _problems = filterService.getFilteredProblems();
      if (_currentIndex >= _problems.length && _problems.isNotEmpty) {
        _currentIndex = 0;
      }
    });
  }

  void _enterReviewMode(List<int> dueIds) {
    // Use the full problem list (not filtered) so due problems are always
    // accessible regardless of any active filters.
    final allProblems = hot100Problems;
    final reviewProblems = dueIds
        .map((id) => allProblems.where((p) => p.id == id).firstOrNull)
        .whereType<LeetCodeProblem>()
        .toList();

    if (reviewProblems.isEmpty) return;

    setState(() {
      _isReviewMode = true;
      _reviewedCount = 0;
      _problems = reviewProblems;
      _currentIndex = 0;
    });
    _pageController.jumpToPage(0);
  }

  void _exitReviewMode() {
    setState(() {
      _isReviewMode = false;
      _reviewedCount = 0;
    });
    _refreshProblems();
    _pageController.jumpToPage(0);
  }

  void _onReviewDone(int problemId) {
    final service = context.read<ProgressService>();
    service.incrementReview(problemId);

    final newCount = _reviewedCount + 1;
    if (newCount >= _problems.length) {
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

  void _goToPrevious() {
    if (_currentIndex > 0) {
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  void _goToNext() {
    if (_currentIndex < _problems.length - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  void _goToRandom() {
    if (_isReviewMode) return;
    if (_problems.isEmpty) return;
    final random = Random().nextInt(_problems.length);
    _pageController.animateToPage(
      random,
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeInOut,
    );
  }

  void _openFilter() async {
    if (_isReviewMode) return;
    final filterService = context.read<FilterService>();
    final String? selectedId = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => ChangeNotifierProvider.value(
        value: filterService,
        child: FilterScreen(problems: hot100Problems),
      ),
    );
    _refreshProblems();
    if (selectedId != null) {
      final idx = _problems.indexWhere((p) => p.id.toString() == selectedId);
      if (idx >= 0) {
        _pageController.jumpToPage(idx);
        setState(() => _currentIndex = idx);
      } else if (_problems.isNotEmpty) {
        _pageController.jumpToPage(0);
        setState(() => _currentIndex = 0);
      }
    } else if (_problems.isNotEmpty) {
      _pageController.jumpToPage(0);
    }
  }

  void _toggleFavorite() {
    if (_isReviewMode) return;
    if (_problems.isEmpty) return;
    final problem = _problems[_currentIndex];
    context.read<ProgressService>().toggleFavorite(problem.id);
    setState(() {});
  }

  void _openStatistics() {
    Navigator.push(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => const StatisticsScreen(),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          const begin = Offset(1.0, 0.0);
          const end = Offset.zero;
          const curve = Curves.easeInOutCubic;
          var tween = Tween(begin: begin, end: end).chain(CurveTween(curve: curve));
          return SlideTransition(position: animation.drive(tween), child: child);
        },
        transitionDuration: const Duration(milliseconds: 300),
      ),
    );
  }

  Widget _buildAnimatedBackground() {
    return AnimatedBuilder(
      animation: _bgController,
      builder: (context, _) {
        return Stack(
          children: [
            // 基础背景
            Container(color: AppTheme.bgDeep),
            // 光源 1：冷雾蓝
            Container(
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  center: _light1.value,
                  radius: 0.7,
                  colors: const [Color(0x205BA4CF), Colors.transparent],
                ),
              ),
            ),
            // 光源 2：暗青绿
            Container(
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  center: _light2.value,
                  radius: 0.7,
                  colors: const [Color(0x204A9E82), Colors.transparent],
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgDeep,
      appBar: AppBar(
        backgroundColor: AppTheme.bgDeep,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: AppTheme.borderLine),
        ),
        leading: _isReviewMode
            ? IconButton(
                icon: const Icon(Icons.arrow_back, color: AppTheme.textSecondary),
                onPressed: _exitReviewMode,
              )
            : null,
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
        actions: [
          Consumer<ProgressService>(
            builder: (context, service, _) {
              final total = _problems.length;
              final completed = _problems.where((p) => service.isCompleted(p.id)).length;
              return Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Center(
                  child: Text(
                    '$completed/$total',
                    style: AppTheme.pixelNumberStyle(size: 15, color: AppTheme.green, weight: FontWeight.bold),
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          // 动态背景层（全屏）
          Positioned.fill(child: _buildAnimatedBackground()),
          // 内容层
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
        ],
      ),
      bottomNavigationBar: Consumer2<ProgressService, FilterService>(
        builder: (context, progressService, filterService, _) {
          final isFav = _problems.isNotEmpty
              ? progressService.isFavorited(_problems[_currentIndex].id)
              : false;
          return BottomToolbar(
            onPrevious: _goToPrevious,
            onNext: _goToNext,
            onRandom: _goToRandom,
            onFilter: _openFilter,
            onFavorite: _toggleFavorite,
            onStatistics: _openStatistics,
            isFavorited: isFav,
            hasActiveFilters: filterService.hasActiveFilters,
          );
        },
      ),
    );
  }

  Widget _buildEmptyState() {
  return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.search_off, size: 64, color: AppTheme.textSecondary),
        const SizedBox(height: 16),
        Text('NO MATCH', style: AppTheme.pixelStyle(size: 12, color: AppTheme.textSecondary)),
        const SizedBox(height: 16),
        GestureDetector(
          onTap: () {
            context.read<FilterService>().resetFilters();
            _refreshProblems();
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            decoration: BoxDecoration(
              border: Border.all(color: AppTheme.blue, width: 2),
            ),
            child: Text('CLEAR FILTERS', style: AppTheme.pixelStyle(size: 10, color: AppTheme.blue)),
          ),
        ),
      ],
    ),
  );
}
}
