import logging
from typing import Type, Mapping, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from faker import Faker

from ugc.common.decorators import gc_collect

logger = logging.getLogger(__name__)

fake = Faker()


class Command(BaseCommand):
    user_cls: Type[User] = get_user_model()

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            '--batch-size',
            dest='batch_size',
            type=int,
            default=100000,
            help='Кол-во объектов для одновременного создания.',
        )
        parser.add_argument(
            '--amount',
            dest='amount',
            type=int,
            default=15000000,
            help='Общее кол-во пользователей.',
        )
        parser.add_argument(
            '--with-passwords',
            dest='with_passwords',
            action='store_true',
            default=False,
            help='Генерировать ли пароли для пользователей. Сильно нагружает CPU, с большим кол-вом будет '
                 'очень долго.',
        )

    # noinspection PyMethodMayBeStatic
    def _generate_params(self, counter: int, with_password: bool) -> Mapping[str, Any]:
        username: str = f'{fake.user_name()}{counter}'
        params: dict[str, Any] = {
            'username': username,
            'email': fake.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
        }
        if with_password:
            params['password'] = make_password(username)
        return params

    @gc_collect
    def _create_users(self, amount: int, start_number: int, with_password: bool):
        self.user_cls.objects.bulk_create(
            self.user_cls(**self._generate_params(
                counter=_ + start_number,
                with_password=with_password,
            ))
            for _ in range(amount)
        )

    def handle(self, *args, **options):
        batch_size: int = options['batch_size']
        amount: int = options['amount']

        logger.info(f'Создаем пользователей: {amount} ...')

        batches: int = amount // batch_size
        if batches > 0:
            for _ in range(batches):
                self._create_users(
                    amount=batch_size,
                    start_number=batch_size * _,
                    with_password=options['with_passwords'],
                )
                logger.info(f'Создано: {batch_size * (_ + 1)}')

        rest: int = amount - batches * batch_size
        if rest > 0:
            self._create_users(
                amount=rest,
                start_number=batches * batch_size,
                with_password=options['with_passwords'],
            )
            logger.info(f'Создано: {amount}')

        logger.info(f'Готово')
