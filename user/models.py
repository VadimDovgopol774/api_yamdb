from django.db import models

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

from core.validators import validate_not_me
from .constants import (
    USERNAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    ROLE_MAX_LENGTH,
    BIO_MAX_LENGTH,
    ROLE_USER,
    ROLE_ADMIN,
    ROLE_MODERATOR
)


class User(AbstractUser):

    class Role(models.TextChoices):
        USER = ROLE_USER, 'User'
        ADMIN = ROLE_ADMIN, 'Admin'
        MODERATOR = ROLE_MODERATOR, 'Moderator'

    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(regex=r'^[\w.@+-]+\Z'),
            validate_not_me,
        ],
    )
    email = models.EmailField(max_length=EMAIL_MAX_LENGTH, unique=True)
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=True, null=True
    )
    last_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True
    )
    bio = models.TextField(blank=True, null=True, max_length=BIO_MAX_LENGTH)
    role = models.CharField(
        choices=Role.choices, default=Role.USER, max_length=ROLE_MAX_LENGTH
    )

    class Meta(AbstractUser.Meta):
        ordering = ('username',)

    @property
    def is_admin(self):
        return (
            self.role == self.Role.ADMIN
            or self.is_superuser
            or self.is_staff
        )

    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR
