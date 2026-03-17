import 'package:flutter/material.dart';
import 'package:path/path.dart' as path;

class CustomMarkdownImage extends StatelessWidget {
  final Uri uri;
  final String recipeDirectory;

  const CustomMarkdownImage({
    super.key,
    required this.uri,
    required this.recipeDirectory,
  });

  String _resolveImagePath() {
    var imagePath = uri.path;

    // Remove leading ./
    if (imagePath.startsWith('./')) {
      imagePath = imagePath.substring(2);
    }

    // If it's a relative path, resolve it relative to recipe directory
    if (!imagePath.startsWith('/')) {
      // recipeDirectory is already relative to assets/recipes/
      // e.g., "dishes/breakfast"
      imagePath = path.join(recipeDirectory, imagePath);
    } else {
      // Remove leading / for absolute paths
      imagePath = imagePath.substring(1);
    }

    // Build full asset path
    // Don't add 'assets/recipes/' prefix since Image.asset expects
    // paths relative to pubspec.yaml asset declarations
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
                '图片加载失败\n原始路径: ${uri.path}\n解析路径: $imagePath\n错误: $error',
                style: const TextStyle(fontSize: 10, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        );
      },
    );
  }
}
