from django.contrib import admin
from cs_activities import models


admin.site.register(models.Activity)
admin.site.register(models.Response)