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
