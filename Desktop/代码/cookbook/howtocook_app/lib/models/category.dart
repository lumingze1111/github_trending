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
