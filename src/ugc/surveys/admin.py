from django.contrib import admin
from django.contrib.admin.widgets import AdminTextInputWidget
from django.utils.translation import gettext_lazy as _

from ugc.common.utils import render_admin_change_link
from ugc.surveys import models
from ugc.surveys.mixins import FormWidgetMixin


class QuestionInline(FormWidgetMixin, admin.TabularInline):
    model = models.Question
    fields = ('get_question', 'text', 'order', 'created_at')
    readonly_fields = ('get_question', 'created_at')
    extra = 0
    max_num = 15
    min_num = 1
    form_widgets = {
        'text': AdminTextInputWidget,
    }

    @admin.display(description=_('к вопросу'))
    def get_question(self, obj):
        return render_admin_change_link(obj, str(_('к вопросу')))


@admin.register(models.Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    readonly_fields = ('created_at', 'author')
    inlines = (QuestionInline,)

    def save_model(self, request, obj: models.Survey, form, change):
        if not change or obj.author_id is None:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class ChoiceInline(FormWidgetMixin, admin.TabularInline):
    model = models.Choice
    fields = ('text', 'order', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0
    max_num = 5
    min_num = 1
    form_widgets = {
        'text': AdminTextInputWidget,
    }


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    fields = ('survey', 'text', 'created_at')
    list_display = ('survey', 'text', 'created_at')
    raw_id_fields = ('survey',)
    readonly_fields = ('created_at',)
    inlines = (ChoiceInline,)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj and obj.pk:
            fields += ('survey',)
        return fields


class SurveyResultChoiceInline(admin.TabularInline):
    model = models.SurveyResultChoice
    fields = ('get_choice_text', 'created_at')
    readonly_fields = ('get_choice_text', 'created_at',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('choice')
        return queryset

    @admin.display(description=_('ответы'))
    def get_choice_text(self, obj):
        return obj.choice.text


@admin.register(models.SurveyResult)
class SurveyResultAdmin(admin.ModelAdmin):
    fields = ('survey', 'user', 'created_at')
    raw_id_fields = ('survey', 'user')
    list_display = ('survey', 'user', 'created_at')
    readonly_fields = ('created_at',)
    inlines = (SurveyResultChoiceInline,)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
