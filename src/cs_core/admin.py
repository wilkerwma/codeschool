from django.contrib import admin
from cs_gallery import models

admin.site.register(models.Gallery)
admin.site.register(models.Submission)