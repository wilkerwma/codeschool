from django.db import models
from django.contrib.auth import models as auth_model
# Create your models here.

# The model to associate two battles
class BattleResult(models.Model):
    date = models.DateField(auto_now_add=True)
    battle_winner = models.OneToOneField('Battle',blank=True,null=True)
    type = "length"

    def determine_winner(self):
        if not self.battle_winner:
            self.battle_winner = getattr(self,'winner_'+self.type)()
            self.save()
        return self.battle_winner

    def winner_length(self):

#       L = sorted([(len(battle.code_winner), battle) for battle in self.battles.all()], key=lambda code_battle: code_battle[0])
        winner = self.battles.first()
        len_code = 0
        for battle in self.battles.all():
            if len_code < len(battle.code_winner):
                len_code = len(battle.code_winner)
                winner = battle
        return winner
        

    def __str__(self):
        if self.battle_winner:
            return "%s (%s) winner: %s" %(self.id,str(self.date),self.battle_winner.user)
        else:
            return "%s (%s)" % (self.id,str(self.date))


class Battle(models.Model):
    """Battle class with attributes necessary to one participation for one challanger"""

    user = models.ForeignKey(auth_model.User)
    time_begin = models.DateTimeField()
    time_end = models.DateTimeField()
    battle_code = models.TextField()

    battle_result = models.ForeignKey(BattleResult,related_name='battles')

    def __str__(self):
        return "Battle %s/%s - %s" % (self.battle_result.id,self.id,self.user)


# Class for invitations
class BattleInvitation(models.Model):
    challangers = models.ManyToManyField(auth_model.User)
    type_battle = models.TextField(default="length")
    status = models.TextField(default="waiting")
 
    def __str__(self):
        return "%s challenge you!" % self.challange

