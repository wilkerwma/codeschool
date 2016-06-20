import copy
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from cs_questions import models


class QuestionBase(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('name', 'short_description', 'owner', 'discipline')
    list_filter = ('discipline', 'owner', 'created', 'modified')
    fieldsets = [
        (None, {
            'fields': (('name', 'author_name'),
                       'discipline',
                       ('owner', 'is_active'),
                       'short_description', 'long_description',),
        }),
        ('Advanced', {
            'classes': ('collapse',),
            'fields': ('comment',),
        }),
    ]

    save_as = True
    save_on_top = True
    search_fields = (
        'name',
        'author_name',
        'short_description',
        'comment',
    )

    @staticmethod
    def _has_comment(obj):
        return bool(obj.comment)


@admin.register(models.CodingIoQuestion)
class CodingIoQuestionAdmin(QuestionBase):
    # Inline models
    class AnswerKeyInline(admin.StackedInline):
        model = models.AnswerKeyItem
        fields = ('language', 'source', 'placeholder', 'is_valid')
        readonly_fields = ('is_valid',)
        extra = 0

    inlines = [AnswerKeyInline]

    # Actions
    def update_answers(self, request, questions):
        for question in questions:
            question.update()
    update_answers.short_description = _('Update answer keys')

    actions = ['update_answers']

    # Overrides and other configurations
    list_display = QuestionBase.list_display + ('answer_keys', 'timeout', 'status')
    fieldsets = copy.deepcopy(QuestionBase.fieldsets)
    fieldsets[0][1]['fields'] += ('iospec_source', 'iospec_size')
    fieldsets[1][1]['fields'] += ('timeout',)

    def answer_keys(self, obj):
        return obj.answer_keys.count()
    answer_keys.short_description = '# keys'


@admin.register(models.QuestionActivity)
class QuestionActivityAdmin(admin.ModelAdmin):

    def recycle_unbound_responses(self, request, qs):
        for activity in qs:
            activity.recycle_unbound_responses()
    recycle_unbound_responses.short_description = _('Recycle unbound responses')

    actions = ['recycle_unbound_responses']


@admin.register(models.QuizActivity)
class QuizActivityAdmin(admin.ModelAdmin):
    class QuizActivityItemInline(admin.TabularInline):
        model = models.QuizActivityItem
        fields = ['question']

    inlines = [QuizActivityItemInline]
    list_display = ('name', 'short_description', 'course', 'responses')

    def responses(self, obj):
        return obj.responses.filter(parent__isnull=True).count()
    responses.short_description = _('# responses')




admin.site.register(models.CodingIoActivity)
admin.site.register(models.NumericQuestion)
admin.site.register(models.AnswerKeyItem)

