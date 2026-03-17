# HowToCook Android App 设计文档

**日期**: 2026-03-17
**项目**: HowToCook 程序员做饭指南 Android 应用
**技术栈**: Flutter

## 项目概述

将 HowToCook 菜谱网站转换为 Android 应用，支持完全离线查看所有菜谱内容。用户无需网络连接即可浏览所有菜谱、查看图片和学习做菜技巧。

## 核心需求

1. **离线查看** - 所有菜谱内容打包进 APK，无需网络
2. **分类浏览** - 按现有分类（家常菜、早餐、主食等）组织内容
3. **Markdown 渲染** - 正确显示菜谱的 Markdown 格式内容和图片
4. **快速开发** - 使用 Flutter 实现跨平台支持

## 技术架构

### 技术选型

- **Flutter 3.x** - 跨平台框架，支持 Android 和 iOS
- **flutter_markdown** - Markdown 内容渲染
- **Assets 打包** - 所有 .md 文件和图片作为 assets 打包

### 项目结构

```
howtocook_app/
├── lib/
│   ├── main.dart                 # 应用入口
│   ├── models/
│   │   ├── category.dart         # 分类数据模型
│   │   └── recipe.dart           # 菜谱数据模型
│   ├── screens/
│   │   ├── home_screen.dart      # 首页（分类列表）
│   │   ├── recipe_list_screen.dart  # 菜谱列表
│   │   └── recipe_detail_screen.dart # 菜谱详情
│   ├── services/
│   │   └── asset_loader.dart     # 加载 assets 文件
│   └── widgets/
│       └── recipe_card.dart      # 菜谱卡片组件
├── assets/
│   └── recipes/                  # 从 HowToCook 复制的所有内容
│       ├── dishes/
│       └── tips/
└── pubspec.yaml                  # 依赖配置
```

## 数据模型

### Category（分类）

```dart
class Category {
  final String id;           // 如 "home-cooking"
  final String name;         // 如 "家常菜"
  final String path;         // 如 "dishes/home-cooking"
  final IconData icon;       // 分类图标
}
```

### Recipe（菜谱）

```dart
class Recipe {
  final String name;         // 菜谱名称
  final String filePath;     // Markdown 文件路径
  final String category;     // 所属分类
}
```

## 页面设计

### 1. 首页（HomeScreen）

**功能**:
- 显示所有分类（家常菜、早餐、主食、汤与粥、饮料、甜品、红烧菜系、半成品加工、酱料）
- 显示"做菜之前"和"进阶知识学习"入口

**布局**:
- GridView 网格布局，每个分类一个卡片
- 卡片包含图标、分类名称、菜谱数量

### 2. 菜谱列表（RecipeListScreen）

**功能**:
- 显示选中分类下的所有菜谱
- 点击进入菜谱详情

**布局**:
- ListView 列表布局
- 每个菜谱显示名称和简短描述（如果有）

### 3. 菜谱详情（RecipeDetailScreen）

**功能**:
- 渲染 Markdown 内容
- 显示菜谱图片
- 支持滚动查看完整内容

**布局**:
- 使用 flutter_markdown 渲染
- 图片使用相对路径加载（从 assets）

## 数据加载策略

### Assets 配置

在 `pubspec.yaml` 中声明所有资源：

```yaml
flutter:
  assets:
    - assets/recipes/dishes/
    - assets/recipes/tips/
```

### 文件加载

```dart
// 加载 Markdown 文件
Future<String> loadRecipe(String path) async {
  return await rootBundle.loadString('assets/recipes/$path');
}

// 加载图片
Image.asset('assets/recipes/dishes/home-cooking/清蒸鲈鱼/清蒸鲈鱼.jpg')
```

### 分类和菜谱索引

硬编码分类结构（基于 README.md 的内容）：

```dart
final categories = [
  Category(
    id: 'home-cooking',
    name: '家常菜',
    path: 'dishes/home-cooking',
    recipes: [
      Recipe(name: '西红柿炒鸡蛋', filePath: 'dishes/home-cooking/西红柿炒鸡蛋.md'),
      Recipe(name: '地三鲜', filePath: 'dishes/home-cooking/地三鲜.md'),
      // ...
    ],
  ),
  // ...
];
```

## 离线支持实现

1. **完全打包** - 所有 Markdown 文件和图片打包进 APK
2. **无网络请求** - 不依赖任何网络 API
3. **本地渲染** - 使用 flutter_markdown 本地渲染内容

## Markdown 渲染

使用 `flutter_markdown` 包：

```dart
Markdown(
  data: markdownContent,
  imageDirectory: 'assets/recipes',
  styleSheet: MarkdownStyleSheet(
    // 自定义样式
  ),
)
```

## 图片处理

- 图片路径需要转换为 Flutter assets 路径
- Markdown 中的相对路径（如 `./清蒸鲈鱼.jpg`）需要解析为完整的 assets 路径

## 依赖包

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_markdown: ^0.6.18
  path: ^1.8.3
```

## 构建和部署

1. **开发环境**: Flutter SDK 3.x
2. **构建 APK**: `flutter build apk --release`
3. **安装**: 生成的 APK 可直接安装到 Android 设备

## 未来扩展

- 搜索功能
- 收藏功能
- 分享菜谱
- 深色模式
- 字体大小调整

## 实施步骤

1. 创建 Flutter 项目
2. 配置 assets（复制所有 Markdown 文件和图片）
3. 实现数据模型和分类索引
4. 实现三个主要页面
5. 测试 Markdown 渲染和图片显示
6. 构建 APK 并测试
