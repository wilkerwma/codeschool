import copy
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from cs_questions import models


class QuestionBase(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('title', 'short_description', 'author_name', '_has_comment')
    list_filter = ('author_name', 'created', 'modified')
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
        fields = ('language', 'source', 'placeholder')
        extra = 0

    inlines = [AnswerKeyInline]

    # Actions
    def remove_computed_answers(self, modeladmin, request, queryset):
        queryset.update(response_computed_template='')
    remove_computed_answers.short_description = 'Remove computed responses'

    actions = ['remove_computed_answers']

    # Overrides and other configurations
    list_display = QuestionBase.list_display + ('timeout',)
    fieldsets = copy.deepcopy(QuestionBase.fieldsets)
    fieldsets[0][1]['fields'] += ('iospec', 'iospec_size')
    fieldsets[1][1]['fields'] += ('timeout',)


@admin.register(models.IoSpecExpansion)
class IoSpecExpansionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'valid_count', 'invalid_count', 'needs_expansion']
    filter_horizontal = ['validated_languages', 'invalid_languages']

    def valid_count(self, obj):
        return obj.validated_languages.count()

    def invalid_count(self, obj):
        return obj.invalid_languages.count()

    def incomplete_count(self, obj):
        return len(obj.get_new_languages())

    valid_count.verbose_name = _('# validated')
    invalid_count.verbose_name = _('# invalid')
    incomplete_count.verbose_name = _('# not analyzed')


admin.site.register(models.QuestionActivity)
admin.site.register(models.CodeIoActivity)
admin.site.register(models.CodeIoFeedback)
