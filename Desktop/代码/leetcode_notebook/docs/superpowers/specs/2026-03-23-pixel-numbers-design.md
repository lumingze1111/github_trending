# 粗像素数字字体设计

**日期：** 2026-03-23
**项目：** LeetCode Hot 100 学习应用
**设计目标：** 在保持当前科技感视觉效果的基础上，为数字显示添加明显的粗像素字体，增强复古游戏风格

---

## 一、设计原则

1. **最小改动** - 仅修改数字显示，其他所有视觉效果保持不变
2. **明显的像素感** - 使用粗像素字体（Silkscreen），类似 8-bit 游戏风格
3. **保持可读性** - 确保数字清晰可辨

---

## 二、字体选择

**选用字体：** Silkscreen

**特点：**
- 粗像素风格，类似经典 8-bit 游戏
- 比 Press Start 2P 更粗、更明显
- 数字显示效果突出
- Google Fonts 提供，易于集成

**备选方案：**
- 如果 Silkscreen 效果不理想，可以考虑 VT323 或其他粗像素字体

---

## 三、改动范围

### 3.1 需要修改的数字显示

**1. 卡片题号（FlipCardWidget）**
- 位置：卡片正面左上角的 `#1`, `#2`, `#3` 等
- 当前字体：`AppTheme.pixelStyle(size: 9)`（Press Start 2P）
- 改为：Silkscreen 字体，字号可能需要调整以匹配粗像素效果

**2. AppBar 进度显示**
- 位置：AppBar 标题下方的 `1 / 100`, `3 / 100` 等
- 当前字体：`AppTheme.monoStyle(size: 11)`（JetBrains Mono）
- 改为：Silkscreen 字体

**3. AppBar 右上角完成数**
- 位置：右上角的 `3/100` 等
- 当前字体：`AppTheme.monoStyle(size: 13, weight: FontWeight.bold)`
- 改为：Silkscreen 字体

### 3.2 保持不变的元素

**所有其他内容保持不变：**
- 题目标题、描述、代码（保持 JetBrains Mono）
- 标签、按钮文字
- 所有边框、阴影、玻璃态效果
- 背景渐变动画
- 颜色方案
- 所有交互效果

---

## 四、实现方案

### 4.1 添加 Silkscreen 字体

在 `pubspec.yaml` 中，Silkscreen 已经通过 `google_fonts` 包可用，无需额外配置。

### 4.2 创建新的字体样式方法

在 `lib/theme/app_theme.dart` 中添加：

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

### 4.3 修改数字显示

**文件 1: `lib/widgets/flip_card_widget.dart`**

找到题号显示部分：
```dart
Text('#${problem.leetcodeId}',
  style: AppTheme.pixelStyle(size: 9, color: AppTheme.blue))
```

改为：
```dart
Text('#${problem.leetcodeId}',
  style: AppTheme.pixelNumberStyle(size: 11, color: AppTheme.blue))
```

**文件 2: `lib/screens/card_learning_screen.dart`**

找到进度显示部分（两处）：

第一处（AppBar 标题下方）：
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

第二处（右上角完成数）：
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

---

## 五、字号调整说明

由于 Silkscreen 字体的视觉大小与 Press Start 2P 和 JetBrains Mono 不同，需要微调字号：

- 题号：从 9 调整到 11（+2）
- 进度显示：从 11 调整到 13（+2）
- 完成数：从 13 调整到 15（+2）

**调整依据：**
- Silkscreen 字体的字符高度比 Press Start 2P 略小，需要增加字号以保持视觉一致性
- 统一增加 2pt 可以保持相对比例关系
- 如果实施后发现数字过大或过小，可以微调 ±1pt

**切换到备选字体的标准：**
- 如果 Silkscreen 在小字号（<11pt）下可读性差，考虑切换到 VT323
- 如果像素感不够明显，考虑增加字号或切换到更粗的字体

---

## 六、实现文件清单

### 6.1 需要修改的文件

1. **lib/theme/app_theme.dart**
   - 添加 `pixelNumberStyle` 方法

2. **lib/widgets/flip_card_widget.dart**
   - 修改题号显示的字体样式

3. **lib/screens/card_learning_screen.dart**
   - 修改进度显示的字体样式（两处）

### 6.2 无需修改的文件

- `pubspec.yaml`（Silkscreen 已通过 google_fonts 可用）
- 其他所有文件

### 6.3 实施顺序建议

**推荐按以下顺序实施，每步完成后立即测试：**

1. **步骤 1：** 在 `app_theme.dart` 中添加 `pixelNumberStyle` 方法
   - 测试：运行应用确保无编译错误

2. **步骤 2：** 修改 `flip_card_widget.dart` 中的题号显示
   - 测试：查看卡片题号是否使用新字体

3. **步骤 3：** 修改 `card_learning_screen.dart` 中的进度显示
   - 测试：查看 AppBar 进度数字是否使用新字体

4. **步骤 4：** 修改 `card_learning_screen.dart` 中的完成数显示
   - 测试：查看右上角完成数是否使用新字体

5. **步骤 5：** 全面测试所有场景（见第七节）

---

## 七、测试验证

### 7.1 视觉验证

- [ ] 题号显示使用粗像素字体，清晰可辨
- [ ] 进度数字使用粗像素字体，与标题文字形成对比
- [ ] 完成数使用粗像素字体，醒目突出
- [ ] 所有其他文字保持原有字体（题目标题、描述、代码等）
- [ ] 整体视觉协调，像素感明显
- [ ] 不同难度题目（Easy/Medium/Hard）的题号显示正常

### 7.2 功能验证

- [ ] 所有数字正常显示
- [ ] 字体加载正常，无回退到 monospace
- [ ] 不同屏幕尺寸下显示正常
- [ ] 筛选状态下的进度显示正常（包括 "(filtered)" 文本）
- [ ] 边界情况测试：
  - [ ] 第一题（1/100）显示正常
  - [ ] 最后一题（100/100）显示正常
  - [ ] 未完成任何题目（0/100）显示正常
  - [ ] 全部完成（100/100）显示正常

### 7.3 性能验证

- [ ] 字体加载不影响应用启动速度
- [ ] 字体切换无明显延迟
- [ ] 在字体加载失败时能正常降级到 monospace

---

## 八、总结

本设计通过最小化改动，仅将数字显示改为粗像素字体（Silkscreen），在保持当前科技感视觉效果的基础上，增加了明显的复古游戏风格。改动范围小、风险低、效果明显。
