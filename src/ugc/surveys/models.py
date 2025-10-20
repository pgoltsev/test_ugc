import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Survey(models.Model):
    title = models.TextField(verbose_name=_('заголовок'))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name=_('автор'))
    first_question = models.ForeignKey('Question', on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name=_('первый вопрос'), related_name='first_question')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата добавления'))

    class Meta:
        verbose_name = _('опрос')
        verbose_name_plural = _('опросы')

    def clean(self):
        # Доп. проверка корректности ссылок.
        if (
            self.first_question_id is not None and
            not Question.objects.filter(id=self.first_question_id, survey_id=self.id).exists()
        ):
            raise ValidationError(
                _('Первый вопрос должен принадлежать текущему опросу с '
                  'id = %(survey_id)d') % {'survey_id': self.id}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{_('Опрос')} {self.id}'


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, verbose_name=_('опрос'))
    text = models.TextField(verbose_name=_('текст вопроса'))
    next = models.ForeignKey('Question', on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name=_('следующий вопрос'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата добавления'))

    class Meta:
        verbose_name = _('вопрос')
        verbose_name_plural = _('вопросы')

    def clean(self):
        # Доп. проверка корректности ссылок.
        if self.next_id is not None:
            if self.next_id == self.id:
                raise ValidationError(_('Следующий вопрос не может быть текущим'))
            if not Question.objects.filter(id=self.next_id, survey_id=self.survey_id).exists():
                raise ValidationError(
                    _('Следующий вопрос должен принадлежать '
                      'тому же опросу с id = %(survey_id)d') % {'survey_id': self.survey_id}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{_('Вопрос')} {self.id}'


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_('вопрос'))
    text = models.TextField(verbose_name=_('текст ответа'))
    order = models.SmallIntegerField(default=0, db_index=True, verbose_name=_('порядок'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата добавления'))

    class Meta:
        verbose_name = _('вариант ответа')
        verbose_name_plural = _('варианты ответов')
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['order', 'created_at']),
        ]

    def __str__(self):
        return f'{_('Вариант ответа')} {self.id}'


class SurveyResult(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text=_('Пользователь, завершивший опрос'),
        verbose_name=_('опрашиваемый'),
    )
    survey = models.ForeignKey(
        Survey,
        on_delete=models.PROTECT,
        verbose_name=_('опрос'),
    )
    current_question = models.ForeignKey(Question, on_delete=models.PROTECT, null=True, blank=True,
                                         verbose_name=_('текущий вопрос'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата добавления'))

    class Meta:
        verbose_name = _('результат опроса')
        verbose_name_plural = _('результаты опросов')
        indexes = [
            models.Index(fields=['user', 'survey']),
        ]

    def __str__(self):
        return f'{_('Результат опроса')} {self.id}'


class SurveyResultChoice(models.Model):
    result = models.ForeignKey(
        SurveyResult,
        on_delete=models.CASCADE,
        verbose_name=_('результат'),
    )
    choice = models.ForeignKey(Choice, on_delete=models.PROTECT, verbose_name=_('ответ'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата добавления'))

    class Meta:
        verbose_name = _('ответ в результате опросов')
        verbose_name_plural = _('ответы в результате опроса')

    def clean(self):
        # Доп. проверка корректности ссылок.
        if self.result.survey_id != self.choice.question.survey_id:
            raise ValidationError(
                _('Опрос в результате должно совпадать с опросом в вопросе выбранного ответа')
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{_('Вариант ответа')} {self.id}'
