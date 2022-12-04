from drf_extra_fields.fields import Base64ImageField
from recipe.models import (AmountIngredient, Favorite, Ingredient, Recipe,
                           ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
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
    id = serializers.IntegerField(source='ingredient.id')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')
    name = serializers.ReadOnlyField(source='ingredient.name')

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
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = AmountIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор представления рецепта.
    """
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = AmountSerializer(many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        read_only_fields = ['author']

    def get_is_favorited(self, obj):
        favorituser = self.context.get('request').user
        if favorituser.is_authenticated:
            return Favorite.objects.filter(
                user=self.context.get('request').user,
                recipe=obj
                ).exists()
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
        queryset=Tag.objects.all(), many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = AddIngredientRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ['author']

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        list_ingredient = []
        for ingredient in ingredients:
            cur_ingredient, status = AmountIngredient.objects.get_or_create(
                ingredient=ingredient['id'], amount=ingredient['amount'])
            list_ingredient.append(cur_ingredient)
        recipe.ingredients.add(*list_ingredient)
        for tag in tags:
            cur_tag = Tag.objects.get(id=tag.id)
            recipe.tags.add(cur_tag)
        return recipe

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data

    def update(self, instance, validated_data):
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredients.clear()
            ingredient_lst = []
            for ingredient in ingredients_data:
                current_ingredient, status = \
                    AmountIngredient.objects.get_or_create(
                    ingredient=ingredient['id'], amount=ingredient['amount'])
                ingredient_lst.append(current_ingredient)
            instance.ingredients.set(ingredient_lst)
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.set(tags_data)
        return instance


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
            instance.recipe, context=context).data


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
            instance.recipe, context=context).data
