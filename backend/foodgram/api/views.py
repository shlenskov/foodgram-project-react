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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ('^name',)


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

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        user = request.user
        favorite_recipe = Favorite.objects.filter(user=user, recipe_id=pk)
        recipe = get_object_or_404(Recipe, id=pk)
        if favorite_recipe.exists():
            return Response({'errors': 'Рецепт уже добавлен в Избранное'},
                            status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.create(user=user, recipe_id=pk)
        serializer = FavoriteRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        user = request.user
        favorite_recipe = Favorite.objects.filter(user=user, recipe_id=pk)
        if favorite_recipe.exists():
            favorite_recipe.delete()
            return Response({'errors': 'Рецепт удален из Избранное'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепта нет в Избранном'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user, recipe_id=pk)
        recipe = get_object_or_404(Recipe, id=pk)
        if shopping_cart.exists():
            return Response(
                {'errors': 'Рецепт уже добавлен в список покупок'},
                status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.create(user=user, recipe_id=pk)
        serializer = FavoriteRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user, recipe_id=pk)
        if shopping_cart.exists():
            shopping_cart.delete()
            return Response({'errors': 'Рецепт удален из списка покупок'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепта нет в списке покупок'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        items = AmountIngredient.objects.select_related('recipe', 'ingredient')
        if request.user.is_authenticated:
            items = items.filter(recipe__shopcart__user=request.user)
        else:
            items = items.filter(recipe_id_in=request.session['purchases'])
        annotate_items = items.annotate(total=Sum('amount')).order_by('-total')
        text = '\n'.join([
            f"{item.ingredient.name} ({item.ingredient.measurement_unit}) "
            f"- {item.total}"
            for item in annotate_items
        ])
        filename = "shopping_cart.txt"
        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
