import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flip_card/flip_card.dart';
import 'package:flip_card/flip_card_controller.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:provider/provider.dart';
import 'package:leetcode_notebook/models/leetcode_problem.dart';
import 'package:leetcode_notebook/services/progress_service.dart';
import 'package:leetcode_notebook/widgets/code_highlight_widget.dart';
import 'package:leetcode_notebook/theme/app_theme.dart';

/// Flip card widget showing problem front and solution back
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

  @override
  State<FlipCardWidget> createState() => _FlipCardWidgetState();
}

class _FlipCardWidgetState extends State<FlipCardWidget> {
  final FlipCardController _controller = FlipCardController();

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: FlipCard(
        controller: _controller,
        flipOnTouch: true,
        speed: 400,
        direction: FlipDirection.HORIZONTAL,
        front: _buildFront(context),
        back: _buildBack(context),
      ),
    );
  }

  Widget _buildFront(BuildContext context) {
    final problem = widget.problem;

    return _PixelCard(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(children: [
              Container(width: 4, height: 32,
                color: AppTheme.difficultyColor(problem.difficulty.name)),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                color: AppTheme.blue.withValues(alpha: 0.15),
                child: Text('#${problem.leetcodeId}',
                  style: AppTheme.pixelNumberStyle(size: 11, color: AppTheme.blue)),
              ),
              const Spacer(),
              Consumer<ProgressService>(builder: (context, service, _) {
                final done = service.isCompleted(problem.id);
                return Icon(done ? Icons.check_circle : Icons.radio_button_unchecked,
                  color: done ? AppTheme.green : AppTheme.textSecondary, size: 22);
              }),
            ]),
            const SizedBox(height: 16),

            // Titles
            Text(problem.titleCn, style: AppTheme.monoStyle(size: 16, weight: FontWeight.bold)),
            Text(problem.title, style: AppTheme.monoStyle(size: 12, color: AppTheme.textSecondary)),
            const SizedBox(height: 12),

            // Tags
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: problem.tags.map((tag) => Chip(
                label: Text(tag, style: AppTheme.monoStyle(size: 10)),
                padding: EdgeInsets.zero,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                visualDensity: VisualDensity.compact,
                side: const BorderSide(color: AppTheme.blue),
                backgroundColor: Colors.transparent,
              )).toList(),
            ),
            const Divider(height: 24, color: AppTheme.gridLine),

            // Description
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(problem.description,
                      style: AppTheme.monoStyle(size: 13).copyWith(height: 1.6)),
                    if (problem.examples.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Text('Examples:', style: AppTheme.monoStyle(size: 12, weight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      ...problem.examples.map((example) => Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(12),
                        decoration: const BoxDecoration(color: AppTheme.bgCardBack),
                        child: Text(example,
                          style: AppTheme.monoStyle(size: 11).copyWith(height: 1.5)),
                      )),
                    ],
                  ],
                ),
              ),
            ),

            // Blink cursor hint
            const SizedBox(height: 8),
            const Center(child: _BlinkingCursor()),
          ],
        ),
      ),
    );
  }

  Widget _buildBack(BuildContext context) {
    final problem = widget.problem;

    return _PixelCard(
      bgColor: AppTheme.bgCardBack,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(children: [
              Text('SOLUTION', style: AppTheme.pixelStyle(size: 11, color: AppTheme.green)),
              const Spacer(),
              _ComplexityBadge(label: 'Time', value: problem.timeComplexity),
              const SizedBox(width: 8),
              _ComplexityBadge(label: 'Space', value: problem.spaceComplexity),
            ]),
            const Divider(height: 20, color: AppTheme.gridLine),

            // Approach + Code
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    MarkdownBody(
                      data: problem.approach,
                      styleSheet: MarkdownStyleSheet(
                        h2: AppTheme.monoStyle(size: 14, weight: FontWeight.bold),
                        h3: AppTheme.monoStyle(size: 13, weight: FontWeight.bold),
                        p: AppTheme.monoStyle(size: 13).copyWith(height: 1.6),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text('Python Code', style: AppTheme.monoStyle(size: 12, weight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    CodeHighlightWidget(code: problem.pythonCode),
                  ],
                ),
              ),
            ),

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
          ],
        ),
      ),
    );
  }
}

class _ComplexityBadge extends StatelessWidget {
  final String label;
  final String value;

  const _ComplexityBadge({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppTheme.blue.withValues(alpha: 0.15),
        border: Border.all(color: AppTheme.blue, width: 1),
      ),
      child: Text(
        '$label: $value',
        style: AppTheme.monoStyle(size: 11, color: AppTheme.blue),
      ),
    );
  }
}

class _PixelCard extends StatelessWidget {
  final Widget child;
  final Color? bgColor;
  const _PixelCard({required this.child, this.bgColor});

  @override
  Widget build(BuildContext context) {
    return Stack(children: [
      Container(
        margin: const EdgeInsets.all(16),
        decoration: AppTheme.pixelBorder().copyWith(
          color: Colors.transparent, // 背景由 BackdropFilter 内层控制
        ),
        child: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              color: (bgColor ?? AppTheme.bgCard).withValues(alpha: 0.92),
              child: child,
            ),
          ),
        ),
      ),
      // 四角装饰点
      Positioned(top: 16, left: 16, child: Container(width: 6, height: 6, color: AppTheme.green)),
      Positioned(top: 16, right: 16, child: Container(width: 6, height: 6, color: AppTheme.green)),
      Positioned(bottom: 16, left: 16, child: Container(width: 6, height: 6, color: AppTheme.green)),
      Positioned(bottom: 16, right: 16, child: Container(width: 6, height: 6, color: AppTheme.green)),
    ]);
  }
}

class _BlinkingCursor extends StatefulWidget {
  const _BlinkingCursor();
  @override State<_BlinkingCursor> createState() => _BlinkingCursorState();
}
class _BlinkingCursorState extends State<_BlinkingCursor>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  @override void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 600))
      ..repeat(reverse: true);
  }
  @override void dispose() { _ctrl.dispose(); super.dispose(); }
  @override Widget build(BuildContext context) => AnimatedBuilder(
    animation: _ctrl,
    builder: (context, _) => Text('▮',
      style: AppTheme.monoStyle(size: 14,
        color: _ctrl.value > 0.5 ? AppTheme.blue : Colors.transparent)),
  );
}
