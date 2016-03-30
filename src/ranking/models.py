from django.db import models
from django.contrib.auth import models as auth_model
# Create your models here.

#Battle class with attributes necessary to one participation for one challanger
class Battle(models.Model):
    user = models.ForeignKey(auth_model.User)
    time_begin = models.DateField()
    time_end = models.DateField()
    code_winner = models.TextField()
    

