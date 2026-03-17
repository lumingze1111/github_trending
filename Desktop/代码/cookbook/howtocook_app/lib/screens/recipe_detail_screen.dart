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
