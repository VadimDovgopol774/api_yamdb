import csv

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.db import IntegrityError, transaction

from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()

list_of_csv = [
    'users',
    'category',
    'genre',
    'titles',
    'review',
    'comments',
]

csv_models_dict = {
    'category': Category,
    'comments': Comment,
    'genre': Genre,
    'review': Review,
    'titles': Title,
    'users': User,
    'author': User,
}


class Command(BaseCommand):
    """Для импорта CSV данных в модели."""
    help = 'Импорт данных из CSV файлов в модели.'

    def handle(self, *args, **options) -> None:
        """Обрабатывает CSV файлы."""
        for csv_file_name in list_of_csv:
            self.process_csv(csv_file_name)

    def process_csv(self, csv_file_name):
        """Чтение и обработка одного CSV файла."""
        print(f'Загрузка {csv_file_name}...', end='')
        try:
            with open(
                f'{settings.CSV_DATA_DIR}/{csv_file_name}.csv',
                encoding='utf-8'
            ) as file:
                objects_list = self.create_objects_list(
                    csv.DictReader(file), csv_file_name
                )
                self.save_objects(objects_list, csv_file_name)
            print('.. ЗАВЕРШЕНО')
        except FileNotFoundError:
            print(
                f'\nОшибка: файл {csv_file_name}.csv не найден в '
                f' {settings.CSV_DATA_DIR}.'
            )
        except Exception as e:
            print(f'\nПроизошла неожиданная ошибка: {e}')

    def create_objects_list(self, reader, csv_file_name):
        """Создает список объектов для импорта."""
        objects_list = []
        for model_data in reader:
            try:
                self.replace_keys_with_objects(model_data, csv_file_name)
                model = csv_models_dict[csv_file_name](**model_data)
                objects_list.append(model)
            except Exception as e:
                print(f'\nОшибка при импорте {csv_file_name}: {e}')
        return objects_list

    def replace_keys_with_objects(self, model_data, csv_file_name):
        """Заменяет ключи на объекты моделей."""
        for key, value in list(model_data.items()):
            if key in csv_models_dict:
                model_data[key] = csv_models_dict[key].objects.get(pk=value)

    def save_objects(self, objects_list, csv_file_name):
        """Сохраняет объекты в базу данных."""
        try:
            with transaction.atomic():
                csv_models_dict[csv_file_name].objects.bulk_create(
                    objects_list
                )
                print('.', end='')
        except IntegrityError as e:
            print(f'\nОшибка целостности для {csv_file_name}: {e}')
