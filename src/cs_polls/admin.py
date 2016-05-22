from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from cs_polls import models


@admin.register(models.Poll)
class PollAdmin(admin.ModelAdmin):
    class OptionInline(admin.TabularInline):
        model = models.Option

    inlines = [OptionInline]
    actions = ['clear_votes']

    def clear_votes(self, request, polls):
        for poll in polls:
            poll.clear_votes()
    clear_votes.short_description = _('Clear all votes')