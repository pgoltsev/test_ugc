from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View

from ugc.surveys.models import Survey, SurveyResult, SurveyResultChoice, Question


class SurveyView(LoginRequiredMixin, View):
    template_name = 'surveys/survey.html'

    def get(self, request, survey_id: int, *args, **kwargs):
        survey: Survey = get_object_or_404(Survey.objects.prefetch_related('question_set__choice_set'), id=survey_id)
        context = {
            'survey': survey,
            'questions': survey.question_set.all(),
        }
        return render(request, self.template_name, context)

    def post(self, request, survey_id: int, *args, **kwargs):
        survey: Survey = get_object_or_404(Survey.objects.prefetch_related('question_set__choice_set'), id=survey_id)

        with transaction.atomic():
            result: SurveyResult = SurveyResult.objects.create(survey=survey, user=request.user)
            for question in survey.question_set.all():
                choice_id = request.POST.get(f"question_{question.id}")
                if choice_id is not None:
                    SurveyResultChoice.objects.create(result=result, choice_id=choice_id)

        return redirect('survey_result', survey_id=survey.id)


class ResultView(LoginRequiredMixin, View):
    template_name = 'surveys/survey_result.html'

    def get(self, request, survey_id: int, *args, **kwargs):
        survey = get_object_or_404(Survey, id=survey_id)
        return render(request, self.template_name, {'survey': survey})


class QuestionView(LoginRequiredMixin, View):
    template_name = 'surveys/survey_questions.html'

    def get(self, request, survey_id: int, question_id: int | None = None):
        filters: dict[str, Any] = {
            'survey_id': survey_id,
        }
        if question_id is not None:
            filters['id'] = question_id
        questions: QuerySet[Question] = Question.objects.prefetch_related('choice_set').filter(**filters)
        context = {
            'questions': questions,
        }
        return render(request, self.template_name, context)
