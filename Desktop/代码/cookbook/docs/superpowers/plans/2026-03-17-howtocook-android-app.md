# HowToCook Android App Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Flutter Android app that displays HowToCook recipes offline with Markdown rendering and image support.

**Architecture:** Flutter app with all recipe Markdown files and images bundled as assets. A build-time tool scans README.md to generate a recipe index. Three main screens: category grid, recipe list, and recipe detail with custom Markdown image loading.

**Tech Stack:** Flutter 3.x, flutter_markdown, Dart path package

---

## Chunk 1: Project Setup and Build Tool

### Task 1: Create Flutter Project

**Files:**
- Create: `howtocook_app/` (new Flutter project)
- Create: `howtocook_app/pubspec.yaml`

- [ ] **Step 1: Create Flutter project**

```bash
cd /Users/lumingze/Desktop/代码/cookbook
flutter create howtocook_app
cd howtocook_app
```

Expected: Flutter project created with default structure

- [ ] **Step 2: Update pubspec.yaml dependencies**

Edit `pubspec.yaml`, replace dependencies section:

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_markdown: ^0.6.18
  path: ^1.8.3
```

- [ ] **Step 3: Get dependencies**

```bash
flutter pub get
```

Expected: Dependencies downloaded successfully

- [ ] **Step 4: Verify project setup**

```bash
flutter doctor
flutter analyze
```

Expected:
- `flutter doctor` shows Flutter SDK installed (Android SDK warnings are acceptable)
- `flutter analyze` shows "No issues found!" or only info-level messages

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: initialize Flutter project with dependencies

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 2: Copy Recipe Assets

**Files:**
- Create: `howtocook_app/assets/recipes/`
- Copy: All files from `../HowToCook/dishes/` and `../HowToCook/tips/`

- [ ] **Step 1: Create assets directory**

```bash
mkdir -p assets/recipes
```

- [ ] **Step 2: Copy recipe content**

```bash
cp -r ../HowToCook/dishes assets/recipes/
cp -r ../HowToCook/tips assets/recipes/
```

Expected: All Markdown files and images copied to assets/recipes/

- [ ] **Step 3: Verify assets copied**

```bash
ls -la assets/recipes/dishes/ | head -10
ls -la assets/recipes/tips/
```

Expected: See dishes/ and tips/ directories with content

- [ ] **Step 4: Commit**

```bash
git add assets/
git commit -m "feat: copy HowToCook recipe assets

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 3: Build Index Generator Tool

**Files:**
- Create: `howtocook_app/tools/generate_index.dart`

- [ ] **Step 1: Create tools directory**

```bash
mkdir -p tools
```

- [ ] **Step 2: Write complete generate_index.dart**

Create `tools/generate_index.dart` with full implementation:

```dart
import 'dart:io';

void main() {
  print('扫描 README.md...');

  final readmePath = '../HowToCook/README.md';
  final readmeFile = File(readmePath);

  if (!readmeFile.existsSync()) {
    print('错误: 找不到 $readmePath');
    exit(1);
  }

  final readme = readmeFile.readAsStringSync();
  final categories = parseReadme(readme);

  print('发现 ${categories.length} 个分类');
  int totalRecipes = 0;
  for (var cat in categories) {
    totalRecipes += (cat['recipes'] as List).length;
  }
  print('发现 $totalRecipes 个菜谱');

  // Validate all files exist
  validateFiles(categories);

  generateIndexFile(categories);
  generateAssetsConfig(categories);

  print('完成！');
}

List<Map<String, dynamic>> parseReadme(String readme) {
  final categories = <Map<String, dynamic>>[];
  final lines = readme.split('\n');

  String? currentCategoryName;
  final recipes = <Map<String, String>>[];

  final iconMap = {
    '家常菜': 'Icons.restaurant',
    '早餐': 'Icons.breakfast_dining',
    '主食': 'Icons.rice_bowl',
    '汤与粥': 'Icons.soup_kitchen',
    '饮料': 'Icons.local_drink',
    '甜品': 'Icons.cake',
    '红烧菜系': 'Icons.local_fire_department',
    '半成品加工': 'Icons.kitchen',
    '酱料和其它材料': 'Icons.water_drop',
  };

  for (var line in lines) {
    if (line.startsWith('### ')) {
      if (currentCategoryName != null && recipes.isNotEmpty) {
        categories.add({
          'id': _toCategoryId(currentCategoryName),
          'name': currentCategoryName,
          'icon': iconMap[currentCategoryName] ?? 'Icons.restaurant',
          'recipes': List.from(recipes),
        });
        recipes.clear();
      }
      currentCategoryName = line.substring(4).trim();
    }

    final recipeMatch = RegExp(r'\* \[(.+?)\]\((.+?)\)').firstMatch(line);
    if (recipeMatch != null && currentCategoryName != null) {
      final name = recipeMatch.group(1)!;
      var path = recipeMatch.group(2)!;
      if (path.startsWith('./')) path = path.substring(2);
      recipes.add({'name': name, 'path': path});
    }
  }

  if (currentCategoryName != null && recipes.isNotEmpty) {
    categories.add({
      'id': _toCategoryId(currentCategoryName),
      'name': currentCategoryName,
      'icon': iconMap[currentCategoryName] ?? 'Icons.restaurant',
      'recipes': List.from(recipes),
    });
  }

  return categories;
}

String _toCategoryId(String name) {
  const idMap = {
    '家常菜': 'home-cooking',
    '早餐': 'breakfast',
    '主食': 'staple',
    '汤与粥': 'soup',
    '饮料': 'drink',
    '甜品': 'dessert',
    '红烧菜系': 'braised',
    '半成品加工': 'semi-finished',
    '酱料和其它材料': 'condiment',
  };
  return idMap[name] ?? name.toLowerCase().replaceAll(' ', '-');
}

void validateFiles(List<Map<String, dynamic>> categories) {
  print('验证文件...');
  var hasErrors = false;

  for (var cat in categories) {
    for (var recipe in cat['recipes'] as List) {
      final mdPath = 'assets/recipes/${recipe['path']}';
      if (!File(mdPath).existsSync()) {
        print('  ✗ 缺失: $mdPath');
        hasErrors = true;
      }
    }
  }

  if (!hasErrors) {
    print('  ✓ 所有 Markdown 文件存在');
  }
}

void generateIndexFile(List<Map<String, dynamic>> categories) {
  final buffer = StringBuffer();
  buffer.writeln('// 自动生成，请勿手动编辑');
  buffer.writeln('// Generated by tools/generate_index.dart');
  buffer.writeln();
  buffer.writeln("import 'package:flutter/material.dart';");
  buffer.writeln("import '../models/category.dart';");
  buffer.writeln("import '../models/recipe.dart';");
  buffer.writeln();
  buffer.writeln('final List<Category> allCategories = [');

  for (var cat in categories) {
    buffer.writeln('  Category(');
    buffer.writeln("    id: '${cat['id']}',");
    buffer.writeln("    name: '${cat['name']}',");
    buffer.writeln("    icon: ${cat['icon']},");
    buffer.writeln('    recipes: [');
    for (var recipe in cat['recipes'] as List) {
      buffer.writeln('      Recipe(');
      buffer.writeln("        name: '${recipe['name']}',");
      buffer.writeln("        filePath: '${recipe['path']}',");
      buffer.writeln("        category: '${cat['id']}',");
      buffer.writeln('      ),');
    }
    buffer.writeln('    ],');
    buffer.writeln('  ),');
  }

  buffer.writeln('];');

  final outputDir = Directory('lib/data');
  if (!outputDir.existsSync()) outputDir.createSync(recursive: true);

  File('lib/data/recipe_index.dart').writeAsStringSync(buffer.toString());
  print('生成 lib/data/recipe_index.dart');
}

void generateAssetsConfig(List<Map<String, dynamic>> categories) {
  final dirs = <String>{'assets/recipes'};

  for (var cat in categories) {
    for (var recipe in cat['recipes'] as List) {
      final path = recipe['path'] as String;
      final dir = path.substring(0, path.lastIndexOf('/'));
      // Add all parent directories
      final parts = ('assets/recipes/$dir').split('/');
      for (var i = 2; i <= parts.length; i++) {
        dirs.add(parts.sublist(0, i).join('/'));
      }
    }
  }

  final sortedDirs = dirs.toList()..sort();
  final buffer = StringBuffer();
  buffer.writeln('  assets:');
  for (var dir in sortedDirs) {
    buffer.writeln('    - $dir/');
  }

  // Write to file for easy copy-paste
  File('assets_config.txt').writeAsStringSync(buffer.toString());
  print('生成 assets 配置 -> assets_config.txt');
}
```

- [ ] **Step 3: Test generate_index.dart**

```bash
dart tools/generate_index.dart
```

Expected output (script must exit with code 0):
```
扫描 README.md...
发现 9 个分类
发现 N 个菜谱
验证文件...
  ✓ 所有 Markdown 文件存在
生成 lib/data/recipe_index.dart
生成 assets 配置 -> assets_config.txt
完成！
```

If any files are missing, output will show:
```
  ✗ 缺失: assets/recipes/path/to/file.md
```
In this case, verify the HowToCook assets were copied correctly in Task 2.

- [ ] **Step 4: Verify generated files**

```bash
head -30 lib/data/recipe_index.dart
cat assets_config.txt | head -20
```

Expected: See generated Dart code with categories and recipes; see assets config

- [ ] **Step 5: Commit**

```bash
git add tools/ lib/data/ assets_config.txt
git commit -m "feat: add recipe index generator tool

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 4: Update pubspec.yaml with Assets

**Files:**
- Modify: `howtocook_app/pubspec.yaml`

- [ ] **Step 1: Copy assets config from generated file**

```bash
cat assets_config.txt
```

- [ ] **Step 2: Add assets to pubspec.yaml**

Edit `pubspec.yaml`, replace the `flutter:` section with the content from `assets_config.txt`:

```bash
# First, view the generated config
cat assets_config.txt
```

Then edit `pubspec.yaml` and replace the `flutter:` section with:

```yaml
flutter:
  uses-material-design: true

  # Paste the content from assets_config.txt here (starting with "assets:")
```

The result should look like:
```yaml
flutter:
  uses-material-design: true

  assets:
    - assets/recipes/
    - assets/recipes/dishes/
    - assets/recipes/dishes/braised/
    - assets/recipes/dishes/braised/红烧肉/
    - assets/recipes/dishes/breakfast/
    # ... (all other directories from assets_config.txt)
```

- [ ] **Step 3: Run flutter pub get**

```bash
flutter pub get
```

Expected: "Got dependencies!" message, no errors about missing assets

- [ ] **Step 4: Verify assets are accessible**

```bash
flutter analyze
```

Expected: No asset-related errors

- [ ] **Step 5: Commit**

```bash
git add pubspec.yaml
git commit -m "feat: configure assets in pubspec.yaml

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: Data Models and Services

### Task 5: Create Data Models

**Files:**
- Create: `howtocook_app/lib/models/recipe.dart`
- Create: `howtocook_app/lib/models/category.dart`

- [ ] **Step 1: Create models directory**

```bash
mkdir -p lib/models
```

- [ ] **Step 2: Write Recipe model**

Create `lib/models/recipe.dart`:

```dart
class Recipe {
  final String name;
  final String filePath;
  final String category;

  const Recipe({
    required this.name,
    required this.filePath,
    required this.category,
  });
}
```

- [ ] **Step 3: Write Category model**

Create `lib/models/category.dart`:

```dart
import 'package:flutter/material.dart';
import 'recipe.dart';

class Category {
  final String id;
  final String name;
  final IconData icon;
  final List<Recipe> recipes;

  const Category({
    required this.id,
    required this.name,
    required this.icon,
    required this.recipes,
  });

  int get recipeCount => recipes.length;
}
```

- [ ] **Step 4: Verify models compile**

```bash
flutter analyze lib/models/
```

Expected: "No issues found!"

- [ ] **Step 5: Commit**

```bash
git add lib/models/
git commit -m "feat: add Recipe and Category data models

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 6: Create Asset Loader Service

**Files:**
- Create: `howtocook_app/lib/services/asset_loader.dart`

- [ ] **Step 1: Create services directory**

```bash
mkdir -p lib/services
```

- [ ] **Step 2: Write AssetLoader service**

Create `lib/services/asset_loader.dart`:

```dart
import 'package:flutter/services.dart';

class AssetLoader {
  /// Load a recipe Markdown file from assets
  static Future<String> loadRecipe(String filePath) async {
    try {
      return await rootBundle.loadString('assets/recipes/$filePath');
    } catch (e) {
      throw Exception('Failed to load recipe: $filePath - $e');
    }
  }

  /// Get the directory path for a recipe (for resolving image paths)
  static String getRecipeDirectory(String filePath) {
    final lastSlash = filePath.lastIndexOf('/');
    if (lastSlash == -1) return '';
    return filePath.substring(0, lastSlash);
  }
}
```

- [ ] **Step 3: Verify service compiles**

```bash
flutter analyze lib/services/
```

Expected: "No issues found!"

- [ ] **Step 4: Commit**

```bash
git add lib/services/
git commit -m "feat: add AssetLoader service for loading recipes

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 7: Create Custom Markdown Image Widget

**Files:**
- Create: `howtocook_app/lib/widgets/custom_markdown_image.dart`

- [ ] **Step 1: Create widgets directory**

```bash
mkdir -p lib/widgets
```

- [ ] **Step 2: Write CustomMarkdownImage widget**

Create `lib/widgets/custom_markdown_image.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:path/path.dart' as path;

class CustomMarkdownImage extends StatelessWidget {
  final Uri uri;
  final String recipeDirectory;

  const CustomMarkdownImage({
    Key? key,
    required this.uri,
    required this.recipeDirectory,
  }) : super(key: key);

  String _resolveImagePath() {
    var imagePath = uri.path;

    // Remove leading ./
    if (imagePath.startsWith('./')) {
      imagePath = imagePath.substring(2);
    }

    // If it's a relative path, resolve it relative to recipe directory
    if (!imagePath.startsWith('/')) {
      imagePath = path.join(recipeDirectory, imagePath);
    }

    // Build full asset path
    final fullPath = path.normalize('assets/recipes/$imagePath');

    return fullPath;
  }

  @override
  Widget build(BuildContext context) {
    final imagePath = _resolveImagePath();

    return Image.asset(
      imagePath,
      errorBuilder: (context, error, stackTrace) {
        return Container(
          padding: const EdgeInsets.all(8.0),
          color: Colors.grey[200],
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.broken_image, size: 48, color: Colors.grey),
              const SizedBox(height: 8),
              Text(
                '图片加载失败: ${uri.path}',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        );
      },
    );
  }
}
```

- [ ] **Step 3: Verify widget compiles**

```bash
flutter analyze lib/widgets/
```

Expected: "No issues found!"

- [ ] **Step 4: Commit**

```bash
git add lib/widgets/
git commit -m "feat: add CustomMarkdownImage widget for recipe images

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```


---

## Chunk 3: UI Screens

### Task 8: Create HomeScreen

**Files:**
- Create: `howtocook_app/lib/screens/home_screen.dart`

- [ ] **Step 1: Create screens directory**

```bash
mkdir -p lib/screens
```

- [ ] **Step 2: Write HomeScreen**

Create `lib/screens/home_screen.dart`:

```dart
import 'package:flutter/material.dart';
import '../data/recipe_index.dart';
import 'recipe_list_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('程序员做饭指南'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 1.2,
        ),
        itemCount: allCategories.length,
        itemBuilder: (context, index) {
          final category = allCategories[index];
          return Card(
            elevation: 2,
            child: InkWell(
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => RecipeListScreen(category: category),
                  ),
                );
              },
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(category.icon, size: 40, color: Theme.of(context).colorScheme.primary),
                    const SizedBox(height: 8),
                    Text(
                      category.name,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${category.recipeCount} 道菜',
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
```

- [ ] **Step 3: Verify compiles**

```bash
flutter analyze lib/screens/home_screen.dart
```

Expected: No issues found

- [ ] **Step 4: Commit**

```bash
git add lib/screens/
git commit -m "feat: add HomeScreen with category grid

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 9: Create RecipeListScreen

**Files:**
- Modify: `howtocook_app/lib/screens/recipe_list_screen.dart`

- [ ] **Step 1: Write RecipeListScreen**

Create `lib/screens/recipe_list_screen.dart`:

```dart
import 'package:flutter/material.dart';
import '../models/category.dart';
import 'recipe_detail_screen.dart';

class RecipeListScreen extends StatelessWidget {
  final Category category;

  const RecipeListScreen({super.key, required this.category});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(category.name),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(8),
        itemCount: category.recipes.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final recipe = category.recipes[index];
          return ListTile(
            leading: Icon(category.icon, color: Theme.of(context).colorScheme.primary),
            title: Text(recipe.name),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => RecipeDetailScreen(recipe: recipe),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

- [ ] **Step 2: Verify compiles**

```bash
flutter analyze lib/screens/recipe_list_screen.dart
```

Expected: No issues found

- [ ] **Step 3: Commit**

```bash
git add lib/screens/recipe_list_screen.dart
git commit -m "feat: add RecipeListScreen

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

### Task 10: Create RecipeDetailScreen

**Files:**
- Create: `howtocook_app/lib/screens/recipe_detail_screen.dart`

- [ ] **Step 1: Write RecipeDetailScreen**

Create `lib/screens/recipe_detail_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../models/recipe.dart';
import '../services/asset_loader.dart';
import '../widgets/custom_markdown_image.dart';

class RecipeDetailScreen extends StatefulWidget {
  final Recipe recipe;

  const RecipeDetailScreen({super.key, required this.recipe});

  @override
  State<RecipeDetailScreen> createState() => _RecipeDetailScreenState();
}

class _RecipeDetailScreenState extends State<RecipeDetailScreen> {
  late Future<String> _contentFuture;

  @override
  void initState() {
    super.initState();
    _contentFuture = AssetLoader.loadRecipe(widget.recipe.filePath);
  }

  @override
  Widget build(BuildContext context) {
    final recipeDir = AssetLoader.getRecipeDirectory(widget.recipe.filePath);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.recipe.name),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: FutureBuilder<String>(
        future: _contentFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('加载失败: ${snapshot.error}'));
          }
          return Markdown(
            data: snapshot.data!,
            imageBuilder: (uri, title, alt) {
              return CustomMarkdownImage(
                uri: uri,
                recipeDirectory: recipeDir,
              );
            },
            styleSheet: MarkdownStyleSheet(
              h1: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              h2: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              p: const TextStyle(fontSize: 15, height: 1.6),
            ),
          );
        },
      ),
    );
  }
}
```

- [ ] **Step 2: Verify compiles**

```bash
flutter analyze lib/screens/recipe_detail_screen.dart
```

Expected: No issues found

- [ ] **Step 3: Commit**

```bash
git add lib/screens/recipe_detail_screen.dart
git commit -m "feat: add RecipeDetailScreen with Markdown rendering

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: Main App Entry and APK Build

### Task 11: Update main.dart

**Files:**
- Modify: `howtocook_app/lib/main.dart`

- [ ] **Step 1: Replace main.dart**

Replace the contents of `lib/main.dart` with:

```dart
import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const HowToCookApp());
}

class HowToCookApp extends StatelessWidget {
  const HowToCookApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '程序员做饭指南',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.orange),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
```

- [ ] **Step 2: Verify full project compiles**

```bash
flutter analyze
```

Expected: No issues found

- [ ] **Step 3: Commit**

```bash
git add lib/main.dart
git commit -m "feat: update main.dart with HowToCookApp entry point

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 12: Build APK

**Files:**
- No new files (build output)

- [ ] **Step 1: Build release APK**

```bash
flutter build apk --release
```

Expected: APK generated at `build/app/outputs/flutter-apk/app-release.apk`

- [ ] **Step 2: Verify APK exists**

```bash
ls -lh build/app/outputs/flutter-apk/app-release.apk
```

Expected: File exists, size > 10MB

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: complete HowToCook Android app implementation

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
