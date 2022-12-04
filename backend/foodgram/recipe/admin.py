from django.contrib import admin

from .models import (AmountIngredient, Favorite, Ingredient, Recipe,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    empty_value_display = '-пусто-'


class AmountIngredientAdmin(admin.TabularInline):
    model = AmountIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'name', 'amount_favorites',
                    'amount_ingredients', 'amount_tags')
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags')
    filter_horizontal = ('ingredients', 'tags')
    empty_value_display = '-пусто-'
    inlines = [
        AmountIngredientAdmin,
    ]

    @staticmethod
    def amount_favorites(obj):
        return obj.favorites.count()

    @staticmethod
    def amount_tags(obj):
        return "\n".join([i[0] for i in obj.tags.values_list('name')])

    @staticmethod
    def amount_ingredients(obj):
        return "\n".join([i[0] for i in obj.ingredients.values_list('name')])


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    empty_value_display = '-пусто-'
