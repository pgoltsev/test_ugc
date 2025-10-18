import sys
from typing import Type

from django.contrib.auth.management.commands.createsuperuser import \
    Command as BaseCommand
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Field


class Command(BaseCommand):
    """Команда создает суперпользователя.

    Делает то же самое, что и 'createsuperuser', но вдобавок не пытается создать, если пользователь уже существует,
    а также может принимать пароль в аргументе.
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            '--if-not-exists',
            dest='if_not_exists',
            action='store_true',
            help='Пользователь создается, только если не существует',
        )
        parser.add_argument(
            '--password',
            help='Пароль. Игнорируется, если команда запушена в интерактивном режиме',
        )

    def get_user_model(self) -> Type[AbstractUser]:
        return getattr(self, 'UserModel')

    def get_username_field(self) -> Field:
        return getattr(self, 'username_field')

    @transaction.atomic
    def handle(self, *args, **options):
        # noinspection PyAttributeOutsideInit
        self._if_not_exists = options['if_not_exists']

        super().handle(*args, **options)

        password = options['password']
        if password:
            database = options['database']
            user_model: Type[AbstractUser] = self.get_user_model()
            # noinspection PyProtectedMember
            manager = user_model._default_manager.db_manager(database)
            username = options[user_model.USERNAME_FIELD]
            user_data = {user_model.USERNAME_FIELD: username}
            user = manager.get(**user_data)
            user.set_password(password)
            user.save()

    def _validate_username(self, username, verbose_field_name, database):
        if self._if_not_exists and self.get_username_field().unique:
            user_model: Type[AbstractUser] = self.get_user_model()
            # noinspection PyUnresolvedReferences
            try:
                # noinspection PyProtectedMember
                user_model._default_manager.db_manager(database).get_by_natural_key(username)
            except user_model.DoesNotExist:
                pass
            else:
                self.stderr.write('Пользователь "{}" уже создан.'.format(username))
                sys.exit(0)

        # noinspection PyUnresolvedReferences,PyProtectedMember
        return super()._validate_username(username, verbose_field_name, database)
