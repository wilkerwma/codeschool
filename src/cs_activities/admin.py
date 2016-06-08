from django.contrib import admin
from cs_activities import models


@admin.register(models.FileDownloadActivity)
class FileDownloadActivityAdmin(admin.ModelAdmin):
    class FileItemInline(admin.TabularInline):
        model = models.FileItem
        fields = ['file', 'name', 'description']

    inlines = [FileItemInline]


admin.site.register(models.Activity)
admin.site.register(models.SyncCodeActivity)
admin.site.register(models.Response)
admin.site.register(models.SourceCodeActivity)
admin.site.register(models.SourceItem)
