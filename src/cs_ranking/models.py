from django.db import models
from django.contrib.auth import models as auth_model
# Create your models here.

class Battle(models.Model):
    """The model to associate two battles"""
    date = models.DateField(auto_now_add=True)
    invitations_user = models.ManyToManyField(auth_model.User)
    battle_winner = models.OneToOneField('BattleResponse',blank=True,null=True)
    question = "1"
    type = "length"
    language="python"   

    def determine_winner(self):
        if not self.battle_winner:
            self.battle_winner = getattr(self,'winner_'+self.type)()
            self.save()
        return self.battle_winner

    def winner_length(self):
        def source_length(battle):
            return len(battle.battle_code)
        return min(self.battles.all(), key=source_length)

    def __str__(self):
        if self.battle_winner:
            return "%s (%s) winner: %s" %(self.id,str(self.date),self.battle_winner.user)
        else:
            return "%s (%s)" % (self.id,str(self.date))


class BattleResponse(models.Model):
    """BattleResponse class with attributes necessary to one participation for one challanger"""

    user = models.ForeignKey(auth_model.User)
    time_begin = models.DateTimeField()
    time_end = models.DateTimeField()
    battle_code = models.TextField()

    battle_result = models.ForeignKey(Battle,related_name='battles')

    def __str__(self):
        return "BattleResponse %s/%s - %s" % (self.battle_result.id,self.id,self.user)


    """# Class for invitations
class BattleResponseInvitation(models.Model):
    challangers = models.ManyToManyField(auth_model.User)
    battle_result = models.OneToOneField(Battle,blank=True,null=True)
    type_battle = models.TextField(default="length")
    status = models.TextField(default="waiting")
 
    def __str__(self):
        return "%s challenge you!" % self.challange
"""
