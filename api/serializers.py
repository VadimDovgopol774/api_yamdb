import datetime

from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.serializers_mixins import UserMixinSerializer
from reviews.models import Category, Comment, Genre, Review, Title
from .constants import USERNAME_RESERVED_VALUE

User = get_user_model()


class UserCreateSerializer(UserMixinSerializer):
    """
    Сериализатор для создания пользователя.
    Проверяет корректность username и email.
    """
    email = serializers.EmailField(max_length=254)

    class Meta:
        model = User
        fields = ('email', 'username')

    def validate_username(self, value):
        if value == USERNAME_RESERVED_VALUE:
            raise serializers.ValidationError(
                f'Использовать "{USERNAME_RESERVED_VALUE}" '
                'в качестве имени запрещено'
            )
        return value


class TokenSerializer(serializers.Serializer):
    """
    Сериализатор для создания токена пользователя.
    Проверяет наличие username и confirmation_code и возвращает JWT токен.
    """
    username = serializers.RegexField(regex=r'^[\w.@+-]+\Z', max_length=150)
    confirmation_code = serializers.CharField(required=True)


class UserAdminEditSerializer(UserMixinSerializer):
    """Сериализатор для редактирования пользователя администратором."""
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role',
        )


class UserEditSerializer(UserAdminEditSerializer):
    """Сериализатор для редактирования пользователем своих данных."""
    role = serializers.CharField(read_only=True)


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев."""
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')


class ReviewSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отзывов. Проверяет, что оценканаходится
    в диапазоне от 1 до 10.
    Запрещает оставлять более одного отзыва на одно и то же
    произведение пользователем.
    """
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )
    score = serializers.IntegerField(min_value=1, max_value=10)

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, data):
        if self.context.get('request').method == 'POST':
            if Review.objects.filter(
                author=self.context.get('request').user,
                title=self.context.get('view').kwargs.get('title_id'),
            ):
                raise serializers.ValidationError(
                    'Не более одного отзыва на одно и то же произведение'
                )
        return data


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий произведений"""
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров произведений."""
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleSerializer(serializers.ModelSerializer):
    """
    Сериализатор для произведений. Включает категорию, жанры и усреднённый
    рейтинг произведения.
    Проверяет, что указанный год не является будущим.
    """
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True, allow_null=False,
        allow_empty=False
    )
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'rating',
            'description',
            'genre',
            'category',
        )

    def validate_year(self, value):
        """Не позволяет добавить будущий год."""
        if value > datetime.date.today().year:
            raise serializers.ValidationError('Нельзя добавлять будущий год')
        return value

    def to_representation(self, instance):
        return GetTitleSerializer(instance, context=self.context).data


class GetTitleSerializer(serializers.ModelSerializer):
    """Сериализатор для получения детальной информации о произведении."""
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'rating',
            'description',
            'genre',
            'category',
        )
