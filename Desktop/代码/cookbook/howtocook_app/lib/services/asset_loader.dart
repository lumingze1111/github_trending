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
