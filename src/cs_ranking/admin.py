from django.contrib import admin
from cs_ranking import models
## Register your models here

# Register model for battle
admin.site.register(models.Battle)
admin.site.register(models.BattleResult)

