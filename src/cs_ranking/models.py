from django.db import models
from django.contrib.auth import models as auth_model
# Create your models here.

# The model to associate two battles
class BattleResult(models.Model):
    date = models.DateField(auto_now_add=True)
    battle_winner = models.OneToOneField('Battle',blank=True,null=True)
    type = "size"

    def determine_winner(self,battles):
        if not self.battle_winner:
            if type == "size":
                index_winner = self.winner_lenght(battles)
                self.battle_winner = battles[index_winner]
                self.save()
        return self.battle_winner

    def winner_lenght(self,battles):
        winner_index=0 # Determine the index of the win ( any number 0..len(battles)-1)
        bigger_length = len(battles.first().code_winner)
        for index in range(1,len(battles)):
            code_length = len(battles[index].code_winner)
            if  code_length < bigger_length:
                bigger_length = code_length
                winner_index
        return winner_index


    def __str__(self):
        if self.battle_winner:
            return "%s (%s) winner: %s" %(self.id,str(self.date),self.battle_winner.user)
        else:
            return "%s (%s)" % (self.id,str(self.date))


#Battle class with attributes necessary to one participation for one challanger
class Battle(models.Model):
    user = models.ForeignKey(auth_model.User)
    time_begin = models.DateTimeField()
    time_end = models.DateTimeField()
    battle_code = models.TextField()

    battle_result = models.ForeignKey(BattleResult,related_name='battles')

    def __str__(self):
        return "Battle %s/%s - %s" % (self.battle_result.id,self.id,self.user)


# Class for invitations
class BattleInvitation(models.Model):
    challanged = models.ForeignKey(auth_model.User,related_name="invitations")
    challange = models.ForeignKey(auth_model.User,related_name="invites")
    type_battle = models.TextField(default="lenght")
    status = models.TextField(default="waiting")

