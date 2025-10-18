from django.urls import path

from .views import SurveyView, ResultView, QuestionView

urlpatterns = [
    # path('<uuid:uid>/', SurveyView.as_view(), name='survey_by_uuid'),
    # path('<uuid:uid>/result/', ResultView.as_view(), name='survey_result_by_uuid'),
    path('<int:survey_id>/', SurveyView.as_view(), name='survey'),
    path('<int:survey_id>/result/', ResultView.as_view(), name='survey_result'),
    path('<int:survey_id>/questions/', QuestionView.as_view(), name='questions_list'),
    path('<int:survey_id>/questions/<int:question_id>/', QuestionView.as_view(), name='question'),
]
