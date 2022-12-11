from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipe.models import (AmountIngredient, Favorite, Ingredient, Recipe,
                           ShoppingCart, Tag)
from users.serializers import CustomUserSerializer


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов.
    """
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ['__all__']


class AmountSerializer(serializers.ModelSerializer):
    """
    Сериализатор для количества ингредиентов.
    """
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )

    class Meta:
        model = AmountIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для тегов.
    """
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ['__all__']


class AddIngredientRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор добавления ингредиентов в рецепт.
    """
    recipe = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        write_only=True,
        min_value=1
    )

    class Meta:
        model = AmountIngredient
        fields = ('recipe', 'id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор представления рецепта.
    """
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = CustomUserSerializer(
        read_only=True
    )
    ingredients = AmountSerializer(
        many=True,
        source='amountingredient'
    )
    image = Base64ImageField(
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField(
        read_only=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        read_only_fields = ['author']

    def get_is_favorited(self, obj):
        favorit_user = self.context.get('request').user
        if favorit_user.is_authenticated:
            return Favorite.objects.filter(
                user=self.context.get('request').user,
                recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        shop_cart_user = self.context.get('request').user
        if shop_cart_user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=self.context.get('request').user,
                recipe=obj
            ).exists()
        return False


class AddRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор добавления рецепта.
    """
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = CustomUserSerializer(
        read_only=True
    )
    ingredients = AddIngredientRecipeSerializer(
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ['author']

    def validate_indredients(self, value):
        if len(value) < 1:
            raise serializers.ValidationError('Добавьте ингредиент.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        create_ingredient = [
            AmountIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        AmountIngredient.objects.bulk_create(create_ingredient)
        return recipe

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()
            create_ingredient = [
                AmountIngredient(
                    recipe=instance,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
            AmountIngredient.objects.bulk_create(create_ingredient)
        return super().update(instance, validated_data)


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор представления добавленного в "Избранное" рецепта.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка покупок.
    """
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe')
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return FavoriteRecipeSerializer(
            instance.recipe, context=context
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка Избранное.
    """
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe')
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return FavoriteRecipeSerializer(
            instance.recipe, context=context
        ).data
