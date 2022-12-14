from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipe.models import (AmountIngredient, Favorite, Ingredient, Recipe,
                           ShoppingCart, Tag)
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .permissions import AuthorOrReadOnly
from .serializers import (AddRecipeSerializer, FavoriteRecipeSerializer,
                          IngredientSerializer, RecipeSerializer,
                          TagSerializer)


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет для работы с ингредиентами.
    """
    # queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ('^name',)

    def get_queryset(self):
        queryset = Ingredient.objects
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__isstartswith=name)
        return queryset.all()


class TagViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет для работы с тегами.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """
    Вьюсет для работы с рецептами.
    """
    queryset = Recipe.objects.all()
    permission_classes = [AuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('tags', 'author')
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
        return AddRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        tags = self.request.query_params.getlist('tags')
        user = self.request.user
        queryset = Recipe.objects
        if tags:
            queryset = queryset.filter_by_tags(tags)
        queryset = queryset.add_user_annotations(user.pk)
        if self.request.query_params.get('is_favorited'):
            queryset = queryset.filter(is_favorited=True)
        if self.request.query_params.get('is_in_shopping_cart'):
            queryset = queryset.filter(is_in_shopping_cart=True)
        author = self.request.query_params.get('author', None)
        if author:
            queryset = queryset.filter(author=author)
        return queryset

    def function_post(self, request, pk, model, error_text):
        user = request.user
        model_recipe = model.objects.filter(user=user, recipe_id=pk)
        recipe = get_object_or_404(Recipe, id=pk)
        if model_recipe.exists():
            return Response(
                {'error': error_text}, status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(user=user, recipe_id=pk)
        serializer = FavoriteRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        error_text = 'Рецепт уже добавлен в Избранное'
        return self.function_post(request, pk, Favorite, error_text)

    def function_delete(self, request, pk, model, delete_text, error400_text):
        user = request.user
        model_recipe = model.objects.filter(user=user, recipe_id=pk)
        if model_recipe.exists():
            model_recipe.delete()
            return Response(delete_text, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': error400_text},
                        status=status.HTTP_400_BAD_REQUEST)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        delete_text = 'Рецепт удален из Избранное'
        error400_text = 'Рецепта нет в Избранном'
        return self.function_delete(request, pk, Favorite, delete_text,
                                    error400_text)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        error_text = 'Рецепт уже добавлен в список покупок'
        return self.function_post(request, pk, ShoppingCart, error_text)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        delete_text = 'Рецепт удален из списка покупок'
        error400_text = 'Рецепта нет в списке покупок'
        return self.function_delete(request, pk, Favorite, delete_text,
                                    error400_text)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        items = AmountIngredient.objects.filter(
            recipe__shopcart__user=request.user
        )
        annotate_items = items.values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total=Sum('amount')).order_by('-total')
        text = '\n'.join([
            f"{item['ingredient__name']} "
            f"({item['ingredient__measurement_unit']}) - {item['total']}"
            for item in annotate_items
        ])
        filename = "shopping_cart.txt"
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
