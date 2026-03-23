# 粗像素数字字体实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为数字显示添加粗像素字体（Silkscreen），增强复古游戏风格

**Architecture:** 在 AppTheme 中添加新的 pixelNumberStyle 方法，然后在3个位置替换数字显示的字体样式。改动最小化，仅影响数字显示。

**Tech Stack:** Flutter, Google Fonts (Silkscreen), Dart

**Spec:** `docs/superpowers/specs/2026-03-23-pixel-numbers-design.md`

---

## 文件结构

### 需要修改的文件

1. **lib/theme/app_theme.dart** (行 29-43)
   - 添加 `pixelNumberStyle` 方法
   - 位置：在 `monoStyle` 方法之后

2. **lib/widgets/flip_card_widget.dart** (行 56-57)
   - 修改题号显示的字体样式
   - 将 `AppTheme.pixelStyle` 改为 `AppTheme.pixelNumberStyle`

3. **lib/screens/card_learning_screen.dart** (两处)
   - 行 208-213：AppBar 进度显示
   - 行 224-229：AppBar 右上角完成数
   - 将 `AppTheme.monoStyle` 改为 `AppTheme.pixelNumberStyle`

---

## Task 1: 添加 pixelNumberStyle 方法

**Files:**
- Modify: `lib/theme/app_theme.dart:29-43`

- [ ] **Step 1: 在 app_theme.dart 中添加 pixelNumberStyle 方法**

在 `monoStyle` 方法之后（第 43 行后）添加：

```dart
static TextStyle pixelNumberStyle({
  double size = 14,
  Color color = textPrimary,
  FontWeight weight = FontWeight.normal
}) {
  try {
    return GoogleFonts.silkscreen(
      fontSize: size,
      color: color,
      fontWeight: weight,
    );
  } catch (_) {
    return TextStyle(
      fontFamily: 'monospace',
      fontSize: size,
      color: color,
      fontWeight: weight,
    );
  }
}
```

- [ ] **Step 2: 验证代码编译**

Run: `flutter analyze lib/theme/app_theme.dart`
Expected: No issues found

- [ ] **Step 3: 提交更改**

```bash
git add lib/theme/app_theme.dart
git commit -m "feat: add pixelNumberStyle method for Silkscreen font

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 修改卡片题号字体

**Files:**
- Modify: `lib/widgets/flip_card_widget.dart:56-57`

- [ ] **Step 1: 修改题号显示的字体样式**

找到第 56-57 行：
```dart
child: Text('#${problem.leetcodeId}',
  style: AppTheme.pixelStyle(size: 9, color: AppTheme.blue)),
```

改为：
```dart
child: Text('#${problem.leetcodeId}',
  style: AppTheme.pixelNumberStyle(size: 11, color: AppTheme.blue)),
```

- [ ] **Step 2: 验证代码编译**

Run: `flutter analyze lib/widgets/flip_card_widget.dart`
Expected: No issues found

- [ ] **Step 3: 热重载测试**

Run: `flutter run` (如果应用已运行，按 `r` 热重载)
Expected: 卡片题号使用 Silkscreen 字体，字号为 11

- [ ] **Step 4: 提交更改**

```bash
git add lib/widgets/flip_card_widget.dart
git commit -m "feat: use Silkscreen font for card problem numbers

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 修改 AppBar 进度显示字体

**Files:**
- Modify: `lib/screens/card_learning_screen.dart:208-213`

- [ ] **Step 1: 修改进度显示的字体样式**

找到第 208-213 行：
```dart
Text(
  filtered
      ? '${_currentIndex + 1} / ${_problems.length} (filtered)'
      : '${_currentIndex + 1} / ${_problems.length}',
  style: AppTheme.monoStyle(size: 11, color: AppTheme.green),
)
```

改为：
```dart
Text(
  filtered
      ? '${_currentIndex + 1} / ${_problems.length} (filtered)'
      : '${_currentIndex + 1} / ${_problems.length}',
  style: AppTheme.pixelNumberStyle(size: 13, color: AppTheme.green),
)
```

- [ ] **Step 2: 验证代码编译**

Run: `flutter analyze lib/screens/card_learning_screen.dart`
Expected: No issues found

- [ ] **Step 3: 热重载测试**

Run: 按 `r` 热重载
Expected: AppBar 进度数字使用 Silkscreen 字体，字号为 13

- [ ] **Step 4: 提交更改**

```bash
git add lib/screens/card_learning_screen.dart
git commit -m "feat: use Silkscreen font for AppBar progress display

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 修改 AppBar 完成数字体

**Files:**
- Modify: `lib/screens/card_learning_screen.dart:224-229`

- [ ] **Step 1: 修改完成数显示的字体样式**

找到第 224-229 行：
```dart
Text(
  '$completed/$total',
  style: AppTheme.monoStyle(size: 13, color: AppTheme.green, weight: FontWeight.bold),
)
```

改为：
```dart
Text(
  '$completed/$total',
  style: AppTheme.pixelNumberStyle(size: 15, color: AppTheme.green, weight: FontWeight.bold),
)
```

- [ ] **Step 2: 验证代码编译**

Run: `flutter analyze lib/screens/card_learning_screen.dart`
Expected: No issues found

- [ ] **Step 3: 热重载测试**

Run: 按 `r` 热重载
Expected: AppBar 右上角完成数使用 Silkscreen 字体，字号为 15

- [ ] **Step 4: 提交更改**

```bash
git add lib/screens/card_learning_screen.dart
git commit -m "feat: use Silkscreen font for AppBar completion count

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 全面测试验证

**Files:**
- Test: All modified files

- [ ] **Step 1: 视觉验证**

测试清单：
- [ ] 题号显示使用粗像素字体，清晰可辨
- [ ] 进度数字使用粗像素字体，与标题文字形成对比
- [ ] 完成数使用粗像素字体，醒目突出
- [ ] 所有其他文字保持原有字体（题目标题、描述、代码等）
- [ ] 整体视觉协调，像素感明显
- [ ] 不同难度题目（Easy/Medium/Hard）的题号显示正常

- [ ] **Step 2: 功能验证**

测试清单：
- [ ] 所有数字正常显示
- [ ] 字体加载正常，无回退到 monospace
- [ ] 不同屏幕尺寸下显示正常
- [ ] 筛选状态下的进度显示正常（包括 "(filtered)" 文本）
- [ ] 边界情况：第一题（1/100）、最后一题（100/100）、未完成（0/100）、全部完成（100/100）

- [ ] **Step 3: 性能验证**

测试清单：
- [ ] 字体加载不影响应用启动速度
- [ ] 字体切换无明显延迟
- [ ] 在字体加载失败时能正常降级到 monospace

- [ ] **Step 4: 最终提交（如果有未提交的更改）**

```bash
git status
# 如果有未提交的更改，提交它们
```

---

## 完成标准

所有任务完成后，应该满足：

1. ✅ `pixelNumberStyle` 方法已添加到 `app_theme.dart`
2. ✅ 卡片题号使用 Silkscreen 字体（字号 11）
3. ✅ AppBar 进度显示使用 Silkscreen 字体（字号 13）
4. ✅ AppBar 完成数使用 Silkscreen 字体（字号 15）
5. ✅ 所有测试验证通过
6. ✅ 所有更改已提交到 git

---

## 故障排除

### 问题 1: 字体加载失败

**症状：** 数字显示为 monospace 而不是 Silkscreen

**解决方案：**
1. 检查网络连接（Google Fonts 需要网络）
2. 检查 `pubspec.yaml` 中是否包含 `google_fonts` 依赖
3. 运行 `flutter pub get` 重新获取依赖

### 问题 2: 字号不合适

**症状：** 数字过大或过小

**解决方案：**
1. 微调字号 ±1pt
2. 参考设计规范第五节的调整依据
3. 如果 Silkscreen 效果不理想，考虑切换到 VT323

### 问题 3: 编译错误

**症状：** `AppTheme.pixelNumberStyle` 未定义

**解决方案：**
1. 确认 Task 1 已完成
2. 运行 `flutter clean && flutter pub get`
3. 重启 IDE/编辑器
