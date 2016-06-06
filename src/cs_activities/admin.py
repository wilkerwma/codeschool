from django.contrib import admin
from cs_activities import models


@admin.register(models.FileDownloadActivity)
class FileDownloadActivityAdmin(admin.ModelAdmin):
    class FileItemInline(admin.TabularInline):
        model = models.FileItem

    inlines = [FileItemInline]


admin.site.register(models.Activity)
admin.site.register(models.SyncCodeActivity)
admin.site.register(models.Response)