import json

from django.db import migrations


def get_json():
    try:
        with open('recipe/data/tags.json', encoding='utf-8') as file:
            initial_tags = json.load(file)
            return initial_tags
    except FileNotFoundError:
        print('Error')


initial_tags = get_json()


def add_tags(apps, schema_editor):
    Tag = apps.get_model("recipe", "Tag")
    for tag in initial_tags:
        new_tag = Tag(**tag)
        new_tag.save()


def remove_tags(apps, schema_editor):
    Tag = apps.get_model("recipe", "Tag")
    for tag in initial_tags:
        Tag.objects.get(slug=tag['slug']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(
            add_tags,
            remove_tags
        )
    ]
