from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .models import Follow, User
from .serializers import CustomUserSerializer, FollowSerializer


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет для работы с пользователями.
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            serializer_class=FollowSerializer)
    def subscribe(self, request, id):
        follow_subscribe = Follow.objects.filter(
            user=request.user,
            author_id=id)
        if request.method == 'POST':
            author = get_object_or_404(User, id=id)
            if follow_subscribe.exists():
                return Response({'errors': 'Вы уже подписаны'},
                                status=status.HTTP_400_BAD_REQUEST)
            if request.user == author:
                return Response(
                    {'errors': 'Вы не можете подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST)
            Follow.objects.create(user=request.user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if follow_subscribe.exists():
            follow_subscribe.delete()
            return Response({'errors': 'Подписка отменена'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Вы не подписаны на пользователя'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[IsAuthenticated],
            serializer_class=FollowSerializer)
    def subscriptions(self, request):
        request = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(request, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
