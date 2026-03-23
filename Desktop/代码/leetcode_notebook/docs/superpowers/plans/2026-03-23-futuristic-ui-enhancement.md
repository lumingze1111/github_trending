# Futuristic UI Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在保持像素艺术风格和主色调的前提下，通过冷调配色调整、玻璃态效果、动态渐变背景和微交互优化，全面提升 LeetCode 学习应用的科技感和沉浸式体验，并修复滑动切换无响应的问题。

**Architecture:** 改动分四个独立层：(1) 主题颜色常量和装饰方法，(2) 翻卡组件（修复交互+玻璃态效果），(3) 主屏幕（动态背景+AppBar），(4) 底部工具栏（玻璃态+微交互）。每层改动互不依赖，可独立提交和验证。

**Tech Stack:** Flutter 3.x, flip_card ^0.7.0, dart:ui (ImageFilter/BackdropFilter), AnimationController, AlignmentTween

---

## 文件结构

| 文件 | 改动类型 | 职责 |
|------|---------|------|
| `lib/theme/app_theme.dart` | 修改 | 颜色常量、pixelBorder 阴影、新增 glassBorder 方法 |
| `lib/widgets/flip_card_widget.dart` | 修改 | flipOnTouch 修复、玻璃态 _PixelCard、翻转按钮、动画参数 |
| `lib/screens/card_learning_screen.dart` | 修改 | 动态渐变背景、AnimationController、AppBar 标题发光 |
| `lib/widgets/bottom_toolbar.dart` | 修改 | 玻璃态容器、按钮点击发光微交互 |

---

## Task 1: 更新主题颜色和阴影系统

**Files:**
- Modify: `lib/theme/app_theme.dart`

### 背景知识

`AppTheme` 是全局主题中心，所有 widget 都从这里取颜色和装饰。目前 `blue = #00B4FF`（亮蓝），`green = #00FF88`（霓虹绿）。
`pixelBorder` 方法当前只有一层 glow 阴影，需要升级为三层阴影。

- [ ] **Step 1: 更新颜色常量**

在 `lib/theme/app_theme.dart` 中，将 `blue` 和 `green` 常量修改为冷调低饱和版本：

```dart
// 将这两行：
static const blue  = Color(0xFF00B4FF);
static const green = Color(0xFF00FF88);

// 改为：
static const blue  = Color(0xFF5BA4CF);  // 冷雾蓝（偏灰，低饱和）
static const green = Color(0xFF4A9E82);  // 暗青绿（冷调，低饱和）
```

- [ ] **Step 2: 升级 pixelBorder 为三层阴影**

将 `pixelBorder` 方法替换为：

```dart
static BoxDecoration pixelBorder({Color borderColor = blue, Color? glowColor}) {
  final glow = glowColor ?? blue;
  return BoxDecoration(
    border: Border.all(color: borderColor, width: 3),
    boxShadow: [
      // 近层：蓝色光晕
      BoxShadow(color: glow.withValues(alpha: 0.30), blurRadius: 15, spreadRadius: 0),
      // 中层：柔和扩散
      BoxShadow(color: glow.withValues(alpha: 0.10), blurRadius: 30, spreadRadius: 5),
      // 远层：深度阴影
      BoxShadow(color: const Color(0x66000000), blurRadius: 40, offset: const Offset(0, 10)),
    ],
  );
}
```

- [ ] **Step 3: 新增 glassBorder 方法（翻转激活状态用）**

在 `pixelBorder` 之后添加：

```dart
// 翻转激活时使用——光晕增强版
static BoxDecoration glassBorderActive({Color borderColor = blue}) {
  return BoxDecoration(
    border: Border.all(color: borderColor, width: 3),
    boxShadow: [
      BoxShadow(color: borderColor.withValues(alpha: 0.60), blurRadius: 15, spreadRadius: 2),
      BoxShadow(color: borderColor.withValues(alpha: 0.20), blurRadius: 30, spreadRadius: 8),
      BoxShadow(color: const Color(0x66000000), blurRadius: 40, offset: const Offset(0, 10)),
    ],
  );
}
```

- [ ] **Step 4: 热重载验证颜色变化**

运行 `flutter run` 后热重载，确认：
- AppBar 标题蓝色变为柔和冷雾蓝
- 卡片边框由亮蓝变为冷雾蓝
- 难度徽章 Easy=暗青绿、Medium=冷雾蓝、Hard=橙色

- [ ] **Step 5: 提交**

```bash
git add lib/theme/app_theme.dart
git commit -m "feat: update theme to cool-toned palette with three-layer shadow"
```

---

## Task 2: 修复翻卡交互问题 + 添加翻转按钮

**Files:**
- Modify: `lib/widgets/flip_card_widget.dart`

### 背景知识

当前 `flipOnTouch: true` 导致整个卡片区域拦截触摸事件，与 `PageView` 水平滑动产生手势竞争。解决方案：`flipOnTouch: false`，改用卡片右下角的专用翻转按钮。

`_PixelCard` 是前后两面卡片共用的外壳，在这里添加玻璃态效果最合适。

`_BlinkingCursor` 目前在 `_buildFront` 的底部——翻转按钮需要放在前后面板相同的位置（右下角）。

注意：`_buildFront` 和 `_buildBack` 返回的是 `_PixelCard`，它用 `Stack` 实现四角装饰点。翻转按钮要作为独立的 `Positioned` 叠加在外层，不能放在 `_PixelCard` 内部（否则点击会触发 Stack 内部的子组件）。

- [ ] **Step 1: 修改 FlipCard 关闭触摸翻转**

在 `_FlipCardWidgetState.build()` 中，将 `flipOnTouch: true` 改为 `false`，`speed: 500` 改为 `400`：

```dart
FlipCard(
  controller: _controller,
  flipOnTouch: false,   // 关键修复：不再拦截触摸事件
  speed: 400,           // 加快翻转（原 500ms）
  direction: FlipDirection.HORIZONTAL,
  front: _buildFront(context),
  back: _buildBack(context),
)
```

- [ ] **Step 2: 将 FlipCard 包在 Stack 中，添加翻转按钮**

将整个 `RepaintBoundary(child: FlipCard(...))` 改为：

```dart
return Stack(
  children: [
    RepaintBoundary(
      child: FlipCard(
        controller: _controller,
        flipOnTouch: false,
        speed: 400,
        direction: FlipDirection.HORIZONTAL,
        front: _buildFront(context),
        back: _buildBack(context),
      ),
    ),
    // 翻转按钮——覆盖在卡片右下角
    Positioned(
      right: 28,
      bottom: 28,
      child: GestureDetector(
        onTap: () => _controller.toggleCard(),
        child: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: AppTheme.blue.withValues(alpha: 0.15),
            border: Border.all(color: AppTheme.blue.withValues(alpha: 0.5), width: 1),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Icon(Icons.flip, size: 20, color: AppTheme.blue),
        ),
      ),
    ),
  ],
);
```

- [ ] **Step 3: 移除 _buildFront 中的 _BlinkingCursor**

`_BlinkingCursor` 在卡片底部起提示作用，但现在右下角已经有翻转按钮，闪烁光标会造成视觉冲突。删除这两行：

```dart
// 删除以下两行（在 _buildFront 底部）：
const SizedBox(height: 8),
const Center(child: _BlinkingCursor()),
```

- [ ] **Step 4: 验证滑动切换**

运行应用，在题目列表中：
- 左右滑动页面，应流畅切换，无拦截
- 点击右下角翻转图标，卡片正常翻转
- 点击卡片空白区域，不再触发翻转

- [ ] **Step 5: 提交**

```bash
git add lib/widgets/flip_card_widget.dart
git commit -m "fix: flipOnTouch false + dedicated flip button, resolves swipe conflict"
```

---

## Task 3: 为卡片添加玻璃态效果

**Files:**
- Modify: `lib/widgets/flip_card_widget.dart`

### 背景知识

`_PixelCard` 是卡片外壳。当前结构：一个带 `pixelBorder` 装饰的 `Container` + 四角装饰点（`Positioned`）。
玻璃态需要 `dart:ui` 的 `ImageFilter`，用 `BackdropFilter` 包裹卡片内容。
注意：`BackdropFilter` 必须在有内容在它后面时才有效果——背景是 `bgDeep` 纯色，效果微弱但存在（给卡片表面增加质感）。

- [ ] **Step 1: 在文件顶部添加 dart:ui 导入**

```dart
import 'dart:ui';
```

- [ ] **Step 2: 重写 _PixelCard 添加玻璃态**

将整个 `_PixelCard` 类替换为：

```dart
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
```

**注意：** `pixelBorder().copyWith(color: ...)` — `BoxDecoration.copyWith` 接受 `color` 参数，这里将颜色设为透明，让 `BackdropFilter` 内层的 `Container` 控制背景色，同时保留三层阴影。

- [ ] **Step 3: 修复 _ComplexityBadge 和 front 面板中硬编码的蓝色**

搜索文件中的 `Color(0x2600B4FF)` 并替换为 `AppTheme.blue.withValues(alpha: 0.15)`（两处）：

第一处在 `_buildFront` 的 `#${problem.leetcodeId}` 容器：
```dart
color: AppTheme.blue.withValues(alpha: 0.15),
```

第二处在 `_ComplexityBadge.build()` 中：
```dart
color: AppTheme.blue.withValues(alpha: 0.15),
```

同理修复 `_ComplexityBadge` 中硬编码的蓝色边框：
```dart
border: Border.all(color: AppTheme.blue, width: 1),
```
（已是使用 `AppTheme.blue`，无需修改——但验证一下）

- [ ] **Step 4: 验证玻璃态外观**

热重载后，卡片应有明显的深度感，边框有三层光晕阴影。

- [ ] **Step 5: 提交**

```bash
git add lib/widgets/flip_card_widget.dart
git commit -m "feat: add glassmorphism effect to flip card with three-layer shadow"
```

---

## Task 4: 主屏幕动态渐变背景 + AppBar 发光

**Files:**
- Modify: `lib/screens/card_learning_screen.dart`

### 背景知识

`_CardLearningScreenState` 已有一个 `PageController`。需要添加一个 `AnimationController` 驱动背景光源动画。

`_CardLearningScreenState` 目前没有混入 `TickerProviderStateMixin`，需要加上（否则无法创建 `AnimationController`）。

`Scaffold` 的 `backgroundColor` 目前是 `AppTheme.bgDeep`。要在背景上叠加渐变层，需要将 `body` 改为 `Stack`，把原本的 `PageView` 放在渐变层上方。

- [ ] **Step 1: 添加 TickerProviderStateMixin**

将类声明改为：

```dart
class _CardLearningScreenState extends State<CardLearningScreen>
    with TickerProviderStateMixin {
```

- [ ] **Step 2: 添加动画 Controller 和动画对象**

在 `_CardLearningScreenState` 顶部添加：

```dart
late AnimationController _bgController;
late Animation<Alignment> _light1;
late Animation<Alignment> _light2;
```

- [ ] **Step 3: 在 initState 中初始化背景动画**

在现有 `initState` 的 `WidgetsBinding.instance.addPostFrameCallback` 之前添加：

```dart
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
```

- [ ] **Step 4: 在 dispose 中释放 Controller**

在 `_pageController.dispose()` 之后添加：

```dart
_bgController.dispose();
```

- [ ] **Step 5: 构建动态渐变背景层**

添加私有方法 `_buildAnimatedBackground()`：

```dart
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
```

- [ ] **Step 6: 修改 build 方法将背景和 body 放入 Stack**

将 `Scaffold` 中的 `body:` 改为：

```dart
body: Stack(
  children: [
    // 动态背景层（全屏）
    Positioned.fill(child: _buildAnimatedBackground()),
    // 内容层
    _problems.isEmpty
        ? _buildEmptyState()
        : PageView.builder(
            controller: _pageController,
            itemCount: _problems.length,
            onPageChanged: (index) {
              setState(() => _currentIndex = index);
            },
            itemBuilder: (context, index) {
              return FlipCardWidget(problem: _problems[index]);
            },
          ),
  ],
),
```

- [ ] **Step 7: 为 AppBar 标题添加发光效果**

在 `build` 方法的 AppBar `title:` 里，找到：

```dart
Text('LeetCode Hot 100', style: AppTheme.pixelStyle(size: 11, color: AppTheme.blue)),
```

替换为：

```dart
Text(
  'LeetCode Hot 100',
  style: AppTheme.pixelStyle(size: 11, color: AppTheme.blue).copyWith(
    shadows: [Shadow(color: AppTheme.blue.withValues(alpha: 0.6), blurRadius: 8)],
  ),
),
```

- [ ] **Step 8: 热重载验证背景动画**

确认：
- 背景有两个缓慢移动的柔和光晕（蓝色和绿色）
- 光晕 20 秒一个周期，来回往复
- AppBar 标题有柔和发光

- [ ] **Step 9: 提交**

```bash
git add lib/screens/card_learning_screen.dart
git commit -m "feat: add animated dual-light background and AppBar glow to main screen"
```

---

## Task 5: 底部工具栏玻璃态 + 微交互

**Files:**
- Modify: `lib/widgets/bottom_toolbar.dart`

### 背景知识

`BottomToolbar` 当前是 `Container`，背景色 `AppTheme.bgDeep`，顶部有 `borderLine` 边框。
要加玻璃态，需要用 `ClipRect` + `BackdropFilter` 包裹，并将背景改为半透明。
`_ToolbarButton` 目前用 `Material + InkWell` 实现点击效果，需要添加点击时的发光微交互。

- [ ] **Step 1: 添加 dart:ui 导入**

在文件顶部添加：

```dart
import 'dart:ui';
```

- [ ] **Step 2: 为 BottomToolbar 添加玻璃态**

将 `BottomToolbar.build()` 中的 `Container(...)` 改为：

```dart
ClipRect(
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
            // ... 原有六个按钮保持不变
          ],
        ),
      ),
    ),
  ),
)
```

- [ ] **Step 3: 为 _ToolbarButton 添加点击发光微交互**

将 `_ToolbarButton` 改为 `StatefulWidget`，以支持点击时的临时发光状态：

```dart
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
```

- [ ] **Step 4: 热重载验证底部工具栏**

确认：
- 工具栏有轻微模糊玻璃态效果
- 点击任意按钮时，图标短暂发光然后恢复
- 激活状态（Filter、Favorite）的发光持续存在

- [ ] **Step 5: 提交**

```bash
git add lib/widgets/bottom_toolbar.dart
git commit -m "feat: add glassmorphism and tap-glow micro-interaction to bottom toolbar"
```

---

## Task 6: 整体回归验证

**Files:**
- 无需修改代码

### 背景知识

所有改动完成后，需要整体验证功能正确性和视觉协调性。

- [ ] **Step 1: 完整功能测试**

逐项验证：
- 左右滑动切换题目：应流畅无卡顿，不再有滑动无响应的问题
- 点击右下角翻转按钮：卡片正常翻转（正面↔背面）
- 点击 Mark as Done 按钮：题目标记完成/取消，图标变化正确
- 点击 Favorite 按钮：收藏状态切换
- 点击 Filter 按钮：筛选面板正常弹出
- 点击 Stats 按钮：统计页面正常跳转
- 点击 Random 按钮：随机跳转到某题

- [ ] **Step 2: 视觉验证清单**

- 难度颜色：Easy（暗青绿）、Medium（冷雾蓝）、Hard（橙色）均清晰可辨
- 卡片边框：冷雾蓝 3px 边框 + 三层光晕阴影，有浮空感
- 玻璃态：卡片背景半透明，动态背景的渐变光晕透过来（若效果微弱属正常，背景本身不够丰富）
- 动态背景：两个光晕缓慢移动，不喧宾夺主
- AppBar 标题：冷雾蓝 + 柔和发光
- 底部工具栏：点击有短暂发光反馈

- [ ] **Step 3: 提交最终验证记录**

```bash
git add .
git commit -m "chore: complete futuristic UI enhancement - all tasks verified"
```
