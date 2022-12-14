import json

from django.db import migrations


def get_json():
    try:
        with open('recipe/data/ingredients.json', encoding='utf-8') as file:
            initial_ingredients = json.load(file)
            return initial_ingredients
    except FileNotFoundError:
        print('Error')


initial_ingredients = get_json()


def add_ingredients(apps, schema_editor):
    Ingredient = apps.get_model("recipe", "Ingredient")
    for ingredient in initial_ingredients:
        new_ingredient = Ingredient(**ingredient)
        new_ingredient.save()


def remove_ingredients(apps, schema_editor):
    Ingredient = apps.get_model("recipe", "Ingredient")
    for ingredient in initial_ingredients:
        Ingredient.objects.get(name=ingredient['name']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0003_add_tags'),
    ]

    operations = [
        migrations.RunPython(
            add_ingredients,
            remove_ingredients
        )
    ]
