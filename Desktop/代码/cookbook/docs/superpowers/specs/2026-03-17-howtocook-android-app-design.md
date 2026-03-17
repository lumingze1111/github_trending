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
│   ├── data/
│   │   └── recipe_index.dart     # 自动生成的菜谱索引
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
│       ├── recipe_card.dart      # 菜谱卡片组件
│       └── markdown_image_builder.dart  # 自定义图片加载器
├── assets/
│   └── recipes/                  # 从 HowToCook 复制的所有内容
│       ├── dishes/
│       └── tips/
├── tools/
│   └── generate_index.dart       # 生成菜谱索引脚本
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
  final List<Recipe> recipes; // 该分类下的所有菜谱
}
```

**分类图标映射表**:
- 家常菜: Icons.restaurant
- 早餐: Icons.breakfast_dining
- 主食: Icons.rice_bowl
- 汤与粥: Icons.soup_kitchen
- 饮料: Icons.local_drink
- 甜品: Icons.cake
- 红烧菜系: Icons.local_fire_department
- 半成品加工: Icons.kitchen
- 酱料: Icons.water_drop
- 做菜之前: Icons.school
- 进阶知识: Icons.auto_stories

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

在 `pubspec.yaml` 中声明所有资源（递归包含所有子目录）：

```yaml
flutter:
  assets:
    - assets/recipes/
    - assets/recipes/dishes/
    - assets/recipes/dishes/home-cooking/
    - assets/recipes/dishes/breakfast/
    - assets/recipes/dishes/staple/
    - assets/recipes/dishes/soup/
    - assets/recipes/dishes/drink/
    - assets/recipes/dishes/dessert/
    - assets/recipes/dishes/braised/
    - assets/recipes/dishes/semi-finished/
    - assets/recipes/dishes/condiment/
    - assets/recipes/tips/
    - assets/recipes/tips/learn/
    - assets/recipes/tips/advanced/
```

**注意**: 所有包含图片的子目录也需要显式声明，例如：
```yaml
    - assets/recipes/dishes/home-cooking/清蒸鲈鱼/
    - assets/recipes/dishes/home-cooking/糖醋鲤鱼/
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

使用 `tools/generate_index.dart` 脚本自动生成索引文件。

**索引生成流程**:

1. 扫描 `../HowToCook/README.md` 文件
2. 解析 Markdown 中的分类和菜谱链接
3. 生成 `lib/data/recipe_index.dart` 文件

**generate_index.dart 实现逻辑**:

```dart
// 1. 读取 README.md
final readme = File('../HowToCook/README.md').readAsStringSync();

// 2. 使用正则表达式提取分类标题和菜谱链接
// 匹配: ### 家常菜
// 匹配: * [西红柿炒鸡蛋](./dishes/home-cooking/西红柿炒鸡蛋.md)

// 3. 生成 Dart 代码
final output = '''
// 自动生成，请勿手动编辑
import 'package:flutter/material.dart';
import '../models/category.dart';
import '../models/recipe.dart';

final List<Category> allCategories = [
  Category(
    id: 'home-cooking',
    name: '家常菜',
    path: 'dishes/home-cooking',
    icon: Icons.restaurant,
    recipes: [
      Recipe(name: '西红柿炒鸡蛋', filePath: 'dishes/home-cooking/西红柿炒鸡蛋.md', category: 'home-cooking'),
      // ...
    ],
  ),
  // ...
];
''';
```

**运行方式**:
```bash
cd howtocook_app
dart tools/generate_index.dart
```

## 离线支持实现

1. **完全打包** - 所有 Markdown 文件和图片打包进 APK
2. **无网络请求** - 不依赖任何网络 API
3. **本地渲染** - 使用 flutter_markdown 本地渲染内容

## Markdown 渲染

使用 `flutter_markdown` 包，配合自定义图片构建器：

```dart
Markdown(
  data: markdownContent,
  imageBuilder: (uri, title, alt) {
    // 自定义图片加载逻辑
    return CustomMarkdownImage(
      uri: uri,
      recipeDirectory: recipeDirectory,
    );
  },
  styleSheet: MarkdownStyleSheet(
    // 自定义样式
  ),
)
```

## 图片处理

### 图片路径解析算法

Markdown 中的图片路径有多种形式：
1. 相对路径: `./清蒸鲈鱼.jpg` 或 `清蒸鲈鱼.jpg`
2. 子目录相对路径: `./清蒸鲈鱼/清蒸鲈鱼.jpg`
3. 绝对路径: `/dishes/home-cooking/清蒸鲈鱼.jpg`

**解析逻辑**:

```dart
String resolveImagePath(String markdownImagePath, String recipeFilePath) {
  // 1. 获取菜谱文件所在目录
  // 例如: recipeFilePath = "dishes/home-cooking/清蒸鲈鱼/清蒸鲈鱼.md"
  // 目录为: "dishes/home-cooking/清蒸鲈鱼"
  final recipeDir = path.dirname(recipeFilePath);

  // 2. 处理相对路径
  if (markdownImagePath.startsWith('./')) {
    markdownImagePath = markdownImagePath.substring(2);
  }

  // 3. 拼接完整路径
  final fullPath = path.join('assets/recipes', recipeDir, markdownImagePath);

  // 4. 规范化路径
  return path.normalize(fullPath);
}
```

**CustomMarkdownImage 实现**:

```dart
class CustomMarkdownImage extends StatelessWidget {
  final Uri uri;
  final String recipeDirectory;

  @override
  Widget build(BuildContext context) {
    final imagePath = resolveImagePath(uri.path, recipeDirectory);

    return Image.asset(
      imagePath,
      errorBuilder: (context, error, stackTrace) {
        return Text('图片加载失败: ${uri.path}');
      },
    );
  }
}
```

### 错误处理

- 如果图片文件不存在，显示占位符和错误信息
- 在构建时验证所有图片引用（通过 generate_index.dart）

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

1. **创建 Flutter 项目**
   ```bash
   flutter create howtocook_app
   cd howtocook_app
   ```

2. **复制 HowToCook 内容到 assets**
   ```bash
   mkdir -p assets/recipes
   cp -r ../HowToCook/dishes assets/recipes/
   cp -r ../HowToCook/tips assets/recipes/
   ```

3. **生成菜谱索引**
   ```bash
   dart tools/generate_index.dart
   ```
   这会生成 `lib/data/recipe_index.dart` 文件

4. **更新 pubspec.yaml**
   - 添加依赖包（flutter_markdown, path）
   - 声明所有 assets 目录（由 generate_index.dart 自动生成配置）

5. **实现核心功能**
   - 数据模型（Category, Recipe）
   - 三个主要页面（Home, RecipeList, RecipeDetail）
   - 自定义图片加载器（CustomMarkdownImage）

6. **测试**
   - 验证所有分类显示正确
   - 验证菜谱 Markdown 渲染正确
   - 验证图片加载正确
   - 测试离线功能（关闭网络）

7. **构建 APK**
   ```bash
   flutter build apk --release
   ```
   生成的 APK 位于 `build/app/outputs/flutter-apk/app-release.apk`

## 构建时工具

### generate_index.dart 完整功能

1. **扫描 README.md**
   - 解析分类标题（### 家常菜）
   - 提取菜谱链接（* [菜名](路径)）

2. **验证文件存在性**
   - 检查所有 .md 文件是否存在
   - 检查 Markdown 中引用的图片是否存在
   - 输出缺失文件警告

3. **生成 recipe_index.dart**
   - 包含所有分类和菜谱的完整索引
   - 包含图标映射

4. **生成 pubspec.yaml assets 配置**
   - 自动发现所有需要声明的目录
   - 输出完整的 assets 配置片段

**运行输出示例**:
```
扫描 README.md...
发现 9 个分类
发现 127 个菜谱
验证文件...
  ✓ 所有 Markdown 文件存在
  ✓ 所有图片文件存在
生成 lib/data/recipe_index.dart
生成 assets 配置（复制到 pubspec.yaml）
完成！
```
