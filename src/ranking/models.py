from django.db import models
from django.contrib.auth import models as auth_model
# Create your models here.

# The model to associate two battles
class BattleResult(models.Model):
    date = models.DateField(auto_now_add=True)
    battle_winner = models.OneToOneField('Battle',blank=True,null=True)

#Battle class with attributes necessary to one participation for one challanger
class Battle(models.Model):
    user = models.ForeignKey(auth_model.User)
    time_begin = models.DateTimeField()
    time_end = models.DateTimeField()
    code_winner = models.TextField()
    
    battle_result = models.ForeignKey(BattleResult,related_name='battles')

    # Return the diff of time in seconds
    def time_result(self):
        try:
            delta_time = (self.time_end - self.time_begin)
            seconds = delta_time.total_seconds()
        except TypeError as e:
            print("error"+str(e))
            seconds = 0.0
        return seconds


