from django.db import models
from django.contrib.auth import models as auth_model
from cs_questions.models import CodingIoQuestion, CodingIoResponse
from cs_core.models import ProgrammingLanguage


# Obs: Mudei para CodingIoBattle pois podem haver outras battles no futuro.
# Talvez CodingBattle deva herdar de uma battle genérica.
class CodingIoBattle(models.Model):
    """The main model that represents a coding battle.

    Users are invited to a battle and shall delivery responses up to some final
    time. Answers are then evaluated and a winner is selected."""

    date = models.DateField(auto_now_add=True)
    invited_users = models.ManyToManyField(auth_model.User, blank=True)
    battle_winner = models.OneToOneField('BattleResponse',blank=True,null=True)
    question = models.ForeignKey(CodingIoQuestion)
    language = models.ForeignKey(ProgrammingLanguage)
    type = "length"   # transforme em um ChoiceField

    def determine_winner(self):
        if not self.battle_winner:
            self.battle_winner = getattr(self, 'winner_' + self.type)()
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


class BattleResponse(CodingIoResponse):
    """BattleResponse class with attributes necessary to one participation for one challenger"""

    time_begin = models.DateTimeField()
    time_end = models.DateTimeField()
    battle = models.ForeignKey(CodingIoBattle,related_name='battles')

    def __str__(self):
        return "BattleResponse %s/%s - %s" % (self.battle.id,self.id,self.user)
