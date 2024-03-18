import datetime

from django.core.exceptions import ValidationError

from api.constants import USERNAME_RESERVED_VALUE


def validate_year(value: int) -> None:
    if value > datetime.date.today().year:
        raise ValidationError('Нельзя добавлять будущий год')


def validate_not_me(value):
    if value.lower() == USERNAME_RESERVED_VALUE:
        raise ValidationError(
            f'Имя пользователя "{USERNAME_RESERVED_VALUE}" недопустимо.'
        )
