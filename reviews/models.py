from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.validators import validate_year
from .constants import (
    NAME_MAX_LENGTH,
    SLUG_MAX_LENGTH,
    REVIEW_TEXT_MAX_LENGTH,
    COMMENT_TEXT_MAX_LENGTH,
    SCORE_MIN_VALUE,
    SCORE_MAX_VALUE,
    COMMENT_STR_MAX_LENGTH,
)

User = get_user_model()


class DateRecordModel(models.Model):
    """Абстрактная базовая модель"""
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('pub_date',)


class UserRelatedModel(models.Model):
    """Абстрактная базовая модель"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    text = models.TextField('Текст', max_length=REVIEW_TEXT_MAX_LENGTH)

    class Meta:
        abstract = True


class Category(models.Model):
    name = models.CharField(
        'Название категории',
        max_length=NAME_MAX_LENGTH,
        help_text='Назовите категорию'
    )
    slug = models.SlugField(
        'Slug категории',
        max_length=SLUG_MAX_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        'Название жанра',
        max_length=NAME_MAX_LENGTH,
        help_text='Назовите жанр'
    )
    slug = models.SlugField(
        'Slug жанра',
        max_length=SLUG_MAX_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'жанр'
        verbose_name_plural = 'Жанры'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(
        'Название произведения',
        max_length=NAME_MAX_LENGTH,
        help_text='Назовите произведение'
    )
    year = models.SmallIntegerField('Год выпуска', validators=(validate_year,))
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='titles',
        verbose_name='Категория'
    )
    genre = models.ManyToManyField(
        Genre, related_name='titles', verbose_name='Жанры'
    )
    description = models.TextField('Описание', blank=True, null=True)

    class Meta:
        verbose_name = 'произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Review(DateRecordModel, UserRelatedModel):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Произведение'
    )
    score = models.PositiveSmallIntegerField(
        'Оценка',
        validators=[
            MinValueValidator(SCORE_MIN_VALUE),
            MaxValueValidator(SCORE_MAX_VALUE)
        ],
        help_text=f'Выберите число от {SCORE_MIN_VALUE} до {SCORE_MAX_VALUE}',
    )

    class Meta:
        verbose_name = 'отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ('pub_date',)
        constraints = (
            models.UniqueConstraint(
                name='unique_review', fields=('author', 'title')
            ),
        )

    def __str__(self):
        return f'{self.title.name}: {self.score}.'


class Comment(DateRecordModel, UserRelatedModel):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Отзыв'
    )
    text = models.TextField('Текст', max_length=COMMENT_TEXT_MAX_LENGTH)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('pub_date',)

    def __str__(self):
        return self.text[:COMMENT_STR_MAX_LENGTH]
