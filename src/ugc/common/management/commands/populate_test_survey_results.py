import logging
import random
from math import floor
from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import Prefetch

from ugc.common.decorators import gc_collect
from ugc.surveys.models import Question, Survey, Choice, SurveyResult, SurveyResultChoice

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            '--batch-size',
            dest='batch_size',
            type=int,
            default=10000,
            help='Кол-во объектов для одновременного создания.',
        )
        parser.add_argument(
            '--surveys-amount',
            dest='surveys_amount',
            type=int,
            default=100000,
            help='Кол-во опросов, для которых создаются результаты.',
        )

    @gc_collect
    def _create_results(
        self,
        amount_per_user: int,
        user_ids: list[int],
        surveys: list[tuple[int, list[tuple[int, list[int]]]]],
    ):
        results: list[SurveyResult] = []
        result_choices: list[SurveyResultChoice] = []

        for user_id in user_ids:
            for _ in range(amount_per_user):
                survey = random.choice(surveys)
                result: SurveyResult = SurveyResult(survey_id=survey[0], user_id=user_id)
                results.append(result)

                questions: list[tuple[int, list[int]]] = survey[1]
                for question in questions:
                    choice_id: int = random.choice(question[1])
                    result_choices.append(SurveyResultChoice(result=result, choice_id=choice_id))

        with transaction.atomic():
            SurveyResult.objects.bulk_create(results)
            SurveyResultChoice.objects.bulk_create(result_choices)

    def handle(self, *args, **options):
        user_cls: Type[User] = get_user_model()
        user_ids: list[int] = list(user_cls.objects.values_list('id', flat=True))
        qs = (
            Survey.objects
            .only('id')
            .prefetch_related(
                Prefetch(
                    'question_set',
                    queryset=Question.objects.only('id', 'survey').prefetch_related(
                        Prefetch(
                            'choice_set',
                            queryset=Choice.objects.only('id', 'question')
                        )
                    )
                )
            )
        )
        surveys: list[tuple[int, list[tuple[int, list[int]]]]] = []
        for survey in qs[:options['surveys_amount']]:
            questions: list[tuple[int, list[int]]] = []
            surveys.append((survey.id, questions))
            for question in survey.question_set.all():
                choices: list[int] = [
                    choice.id
                    for choice in question.choice_set.all()
                ]
                questions.append((question.id, choices))

        logger.info(f'Создаем результаты ...')

        length: int = len(user_ids)
        batch_size: int = min(options['batch_size'], length)
        start_idx: int = 0
        end_idx: int
        while start_idx < length:
            end_idx = start_idx + batch_size
            user_batch: list[int] = user_ids[start_idx:end_idx]
            self._create_results(amount_per_user=5, user_ids=user_batch, surveys=surveys)
            start_idx = end_idx
            logger.info(f'Создано {start_idx} | {floor(start_idx * 100 / length)}%')

        logger.info(f'Готово')
