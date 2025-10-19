from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.views import View

from ugc.surveys.models import Survey, SurveyResult, SurveyResultChoice, Question, Choice


class SurveyView(LoginRequiredMixin, View):
    template_name = 'surveys/survey.html'

    def get(self, request, survey_id: int, *args, **kwargs):
        survey: Survey = get_object_or_404(
            Survey.objects.select_related(
                'first_question',
            ).prefetch_related(
                'question_set__choice_set',
            ),
            pk=survey_id,
        )

        result: SurveyResult | None = SurveyResult.objects.select_related('current_question').filter(
            survey_id=survey_id,
            user=request.user,
        ).first()
        current_question: Question | None = result.current_question if result else survey.first_question

        context = {
            'survey': survey,
            'question': current_question,
        }
        return render(request, self.template_name, context)

    def post(self, request, survey_id: int, *args, **kwargs):
        choice_id: str | None = request.POST.get('choice')
        choice: Choice = get_object_or_404(Choice.objects.select_related('question'), pk=choice_id)

        with transaction.atomic():
            next_question_id: int = choice.question.next_id
            result, created = SurveyResult.objects.get_or_create(
                survey_id=survey_id, user=request.user,
                defaults={'current_question_id': next_question_id},
            )
            if not created:
                result.current_question_id = next_question_id
                result.save()

            SurveyResultChoice.objects.create(result=result, choice_id=choice_id)

        return self.get(request, survey_id, *args, **kwargs)
