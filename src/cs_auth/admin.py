from cs_auth import models
from django.contrib import admin
from cs_auth import models


@admin.register(models.CustomFieldCategory)
class CustomFieldCategoryAdmin(admin.ModelAdmin):
    class CustomFieldDefinitionAdmin(admin.TabularInline):
        model = models.CustomFieldDefinition

    inlines = [CustomFieldDefinitionAdmin]


admin.site.register(models.FriendshipStatus)
admin.site.register(models.Profile)