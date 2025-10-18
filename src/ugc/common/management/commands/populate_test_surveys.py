import logging
import random
from typing import Type, TypeVar

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction

from ugc.common.decorators import gc_collect
from ugc.surveys.models import Question, Survey, Choice

logger = logging.getLogger(__name__)

WORDS = ['lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'lelit']


def generate_random_text(min_words_cnt: int = 5, max_words_cnt: int = 15) -> str:
    words_cnt: int = random.randint(min_words_cnt, max_words_cnt)
    return ' '.join([WORDS[random.randint(0, len(WORDS) - 1)] for _ in range(words_cnt)])


T = TypeVar('T')


def generate_entities(min_cnt: int, max_cnt: int, cls: Type[T], **params) -> list[T]:
    result: list[T] = []
    cnt: int = random.randint(min_cnt, max_cnt)
    orders: list[int] = random.sample(range(0, cnt), cnt)
    for idx, _ in enumerate(range(cnt)):
        text: str = generate_random_text()
        entity: T = cls(text=text, order=orders[idx], **params)
        result.append(entity)
    return result


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            '--batch-size',
            dest='batch_size',
            type=int,
            default=20000,
            help='Кол-во объектов для одновременного создания.',
        )
        parser.add_argument(
            '--amount',
            dest='amount',
            type=int,
            default=1000000,
            help='Общее кол-во опросов.',
        )

    @gc_collect
    def _create_surveys(self, amount: int, user_ids: list[int]):
        surveys: list[Survey] = [
            Survey(title=generate_random_text(), author_id=random.choice(user_ids))
            for _ in range(amount)
        ]
        questions: list[Question] = []
        choices: list[Choice] = []

        for survey in surveys:
            survey_questions: list[Question] = generate_entities(5, 15, Question, survey=survey)
            questions.extend(survey_questions)

            for question in survey_questions:
                choices.extend(generate_entities(3, 5, Choice, question=question))

        with transaction.atomic():
            Survey.objects.bulk_create(surveys)
            Question.objects.bulk_create(questions)
            Choice.objects.bulk_create(choices)

    def handle(self, *args, **options):
        user_cls: Type[User] = get_user_model()
        user_ids: list[int] = list(user_cls.objects.values_list('id', flat=True))

        batch_size: int = options['batch_size']
        amount: int = options['amount']
        batches: int = amount // batch_size

        logger.info(f'Создаем опросы: {amount} ...')

        if batches > 0:
            for _ in range(batches):
                self._create_surveys(amount=batch_size, user_ids=user_ids)
                logger.info(f'Создано: {batch_size * (_ + 1)}')

        rest: int = amount - batches * batch_size
        if rest > 0:
            self._create_surveys(amount=rest, user_ids=user_ids)
            logger.info(f'Создано: {amount}')

        logger.info(f'Готово')
