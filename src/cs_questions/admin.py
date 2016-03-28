import copy
from django.contrib import admin
from cs_questions import models


class QuestionBase(admin.ModelAdmin):
    date_hierarchy = 'timestamp'
    list_display = ('title', 'short_description', 'author_name', '_has_comment')
    list_filter = ('author_name', 'timestamp')
    fieldsets = [
        (None, {
            'fields': (('title', 'author_name'),
                       'discipline',
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
        'title',
        'author_name',
        'short_description',
        'comment',
    )

    @staticmethod
    def _has_comment(obj):
        return bool(obj.comment)


@admin.register(models.CodeIoQuestion)
class CodeIoQuestionAdmin(QuestionBase):
    # Inline models
    class AnswerKeyInline(admin.StackedInline):
        model = models.CodeIoAnswerKey
        extra = 0
        fieldsets = (
            (None, {
                'fields': ('language', 'source_code'),
            }),
            ('Advanced', {
                'classes': ('collapse',),
                'fields': ('placeholder',),
            }),

        )

    inlines = [AnswerKeyInline]

    # Actions
    def remove_computed_answers(self, modeladmin, request, queryset):
        queryset.update(response_computed_template='')
    remove_computed_answers.short_description = 'Remove computed responses'

    actions = ['remove_computed_answers']

    # Overrides and other configurations
    list_display = QuestionBase.list_display + ('timeout',)
    fieldsets = copy.deepcopy(QuestionBase.fieldsets)
    fieldsets[0][1]['fields'] += ('iospec',)
    fieldsets[1][1]['fields'] += ('timeout',)
    fieldsets.append(
        ('Debug', {
            'classes': ('collapse',),
            'fields': ('iospec_expanded',),
        })
    )


admin.site.register(models.QuestionActivity)
admin.site.register(models.CodeIoActivity)
admin.site.register(models.CodeIoFeedback)
