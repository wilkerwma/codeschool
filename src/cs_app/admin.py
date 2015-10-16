from django.contrib import admin
from . import models

class QuestionAnswerInline(admin.StackedInline):
    model = models.QuestionAnswer
    extra = 0

class QuestionPlaceholderInline(admin.StackedInline):
    model = models.QuestionPlaceholder
    extra = 0

@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'short_description', 'description', 'visible'),
        }),
        ('Avançado', {
            #'classes': ('collapse',),
            'fields': ('question_type', 'grading'),
        }),
    )
    
    inlines = (QuestionAnswerInline, QuestionPlaceholderInline) 
    
# Register classes
admin.site.register(models.Discipline)
admin.site.register(models.Quiz)
admin.site.register(models.Response)

