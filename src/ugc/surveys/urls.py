from django.urls import path

from .views import SurveyView

urlpatterns = [
    path('<int:survey_id>/', SurveyView.as_view(), name='survey'),
]
