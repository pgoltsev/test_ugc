from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models.query import Prefetch
from django.http.response import Http404
from django.shortcuts import render
from django.views import View

from ugc.surveys.models import Survey, SurveyResult, SurveyResultChoice, Question, Choice


def get_survey(user_id: int, survey_id: int) -> Survey | None:
    return Survey.objects.prefetch_related(
        Prefetch(
            'question_set',
            queryset=Question.objects.prefetch_related(
                Prefetch(
                    'choice_set',
                    queryset=Choice.objects.order_by('order', 'created_at'),
                )
            ).order_by('order', 'created_at'),
        )
    ).filter(
        id=survey_id,
    ).first()


def get_current_question(user_id: int, survey: Survey) -> Question | None:
    answered_choice_ids: set[int] = get_survey_result_choice_ids(user_id=user_id, survey_id=survey.id)
    # Находим первый неотвеченный вопрос.
    for question in survey.question_set.all():
        question_choice_ids: set[int] = set(choice.id for choice in question.choice_set.all())
        if question_choice_ids & answered_choice_ids:
            continue

        return question

    return None


def get_survey_result_choice_ids(user_id: int, survey_id: int) -> set[int]:
    result: SurveyResult | None = SurveyResult.objects.prefetch_related(
        Prefetch(
            'surveyresultchoice_set',
            SurveyResultChoice.objects.only('choice_id'),
        )
    ).filter(
        survey_id=survey_id,
        user_id=user_id,
    ).first()

    ids = set()
    if result:
        for choice in result.surveyresultchoice_set.all():
            ids.add(choice.choice_id)
    return ids


class SurveyView(LoginRequiredMixin, View):
    template_name = 'surveys/survey.html'

    def get(self, request, survey_id: int, *args, **kwargs):
        user_id: int = request.user.id

        survey: Survey | None = get_survey(user_id=user_id, survey_id=survey_id)
        if survey is None:
            raise Http404

        current_question: Question | None = get_current_question(user_id=user_id, survey=survey)
        context = {
            'survey': survey,
            'question': current_question,
        }
        return render(request, self.template_name, context)

    def post(self, request, survey_id: int, *args, **kwargs):
        choice_id: str = request.POST.get('choice')
        if choice_id is None:
            raise Http404

        result: SurveyResult
        with transaction.atomic():
            result, _ = SurveyResult.objects.get_or_create(survey_id=survey_id, user=request.user)
            SurveyResultChoice.objects.create(result=result, choice_id=choice_id)

        return self.get(request, survey_id, *args, **kwargs)
