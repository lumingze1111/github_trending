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
