from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api.filters import TitleFilter
from api.base_viewsets import BaseCreateListDestroyViewSet
from api.permissions import (
    IsAdminOrReadOnly,
    IsAdmin,
    IsAuthorOrAdminOrReadOnly,
)
from api.serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    GetTitleSerializer,
    ReviewSerializer,
    TitleSerializer,
    TokenSerializer,
    UserAdminEditSerializer,
    UserCreateSerializer,
    UserEditSerializer,
)
from api.utils import send_email_to_user
from reviews.models import Category, Genre, Title, Review

User = get_user_model()


class CreateUserView(CreateAPIView):
    """
    Представление для создания пользователя.
    Отправляет код подтверждения на email пользователя.
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = User.objects.get_or_create(**serializer.validated_data)
        token = default_token_generator.make_token(user)
        send_email_to_user(email=user.email, code=token)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateJWTTokenView(CreateAPIView):
    """
    Представление для создания JWT токена по коду подтверждения,
    отправленному на email пользователя.
    """
    serializer_class = TokenSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, username=serializer.validated_data['username']
        )
        token = serializer.validated_data['confirmation_code']
        if default_token_generator.check_token(user, token):
            token = AccessToken.for_user(user)
            return Response({'token': str(token)}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    Представление для управления пользователями.
    Доступно только администраторам.
    """
    queryset = User.objects.all()
    serializer_class = UserAdminEditSerializer
    permission_classes = (IsAdmin,)
    filter_backends = (filters.SearchFilter,)
    lookup_field = 'username'
    search_fields = ('username',)
    pagination_class = PageNumberPagination
    http_method_names = ['get', 'post', 'delete', 'patch']

    @action(
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,),
        detail=False,
        serializer_class=UserEditSerializer,
        url_path='me',
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @me.mapping.patch
    def patch_me(self, request):
        user = request.user
        serializer = self.get_serializer(
            user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    """
    Представление для управления комментариями к отзывам.
    Позволяет создавать, просматривать, редактировать и удалять комментарии.
    """
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'delete', 'patch']

    def get_review(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        return get_object_or_404(Review, pk=review_id, title_id=title_id)

    def get_queryset(self):
        return self.get_review().comments.select_related('author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Представление для управления отзывами на произведения.
    Позволяет создавать, просматривать, редактировать и удалять отзывы.
    """
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    http_method_names = ['get', 'post', 'delete', 'patch']

    def get_title(self):
        return get_object_or_404(Title, pk=self.kwargs.get('title_id'))

    def get_queryset(self):
        return self.get_title().reviews.select_related('author')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CategoryViewSet(BaseCreateListDestroyViewSet):
    """
    Представление для управления категориями произведений.
    Позволяет создавать, просматривать список и удалять категории.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(BaseCreateListDestroyViewSet):
    """
    Представление для управления жанрами произведений.
    Позволяет создавать, просматривать список и удалять жанры.
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    """
    Представление для управления произведениями.
    Позволяет создавать, просматривать, обновлять и удалять произведения.
    """
    queryset = (
        Title
        .objects
        .prefetch_related('genre', 'category')
        .annotate(rating=Avg('reviews__score'))
        .order_by('name')
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = PageNumberPagination
    http_method_names = ['get', 'post', 'delete', 'patch']

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return GetTitleSerializer
        return TitleSerializer
