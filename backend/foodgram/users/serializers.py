from djoser.serializers import UserCreateSerializer
from recipe.models import Recipe
from rest_framework import serializers

from .models import Follow, User


class CustomUserSerializer(UserCreateSerializer):
    """
    Сериализатор представления пользователя.
    """
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=obj.id).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Сериализатор регистрации пользователя.
    """
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор представления добавленного в "Избранное" рецепта.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(CustomUserSerializer):
    """
    Сериализатор представления подписок пользователя.
    """
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        limit_param = self.context['request'].query_params
        count_recipes = int(limit_param.get('recipes_limit',
                                            obj.recipes.count()))
        queryset = obj.recipes.all()[:count_recipes]
        return FavoriteRecipeSerializer(many=True).to_representation(queryset)

    def get_recipes_count(self, obj):
        return obj.recipes.count()
