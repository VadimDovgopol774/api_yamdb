from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.validators import validate_not_me
from .constants import USERNAME_MAX_LENGTH

User = get_user_model()


class UserMixinSerializer(serializers.ModelSerializer):
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=USERNAME_MAX_LENGTH,
        validators=[validate_not_me]
    )

    def validate(self, data):
        if User.objects.filter(
            username=data.get('username'), email=data.get('email')
        ):
            return data
        elif User.objects.filter(username=data.get('username')):
            raise serializers.ValidationError(
                'Имя пользователя уже занято'
            )
        elif User.objects.filter(email=data.get('email')):
            raise serializers.ValidationError(
                'Адрес электронной почты уже занят'
            )
        return data
