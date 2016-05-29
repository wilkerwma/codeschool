from django.db import models
from django.contrib.auth import models as auth_model
from django.core.urlresolvers import reverse
from cs_questions.models import Question
from cs_core.models import ProgrammingLanguage
from cs_questions.models import CodingIoQuestion, CodingIoResponse

class Battle(models.Model):
    """The model to associate many battles"""
    TYPE_BATTLES = ( (0,"length"),(1,"time") )
    date = models.DateField(auto_now_add=True)
    invitations_user = models.ManyToManyField(auth_model.User)
    battle_owner = models.ForeignKey(auth_model.User,related_name="battle_owner")
    battle_winner = models.OneToOneField('BattleResponse',blank=True,null=True,related_name="winner")
    question = models.ForeignKey(CodingIoQuestion,related_name="battle_question")
    type = models.IntegerField(default=0,choices=TYPE_BATTLES)
    language = models.ForeignKey(ProgrammingLanguage, related_name="battle_language")
    short_description = "ha"
    long_description = "ho"

    def determine_winner(self):
        if not self.battle_winner and self.battles.first():
            self.battle_winner = getattr(self,'winner_'+self.type)()
            self.save()
        return self.battle_winner

    def winner_length(self):
        def source_length(battle):
            return len(battle.source)
        return min(self.battles.all(), key=source_length)

    def get_absolute_url(self):
        return reverse("figths:battle",kwargs={'battle_pk': self.pk})

    def __str__(self):
        if self.battle_winner:
            return "%s (%s) winner: %s" %(self.id,str(self.date),self.battle_winner.user)
        else:
            return "%s (%s)" % (self.id,str(self.date))


class BattleResponse(CodingIoResponse):
    """BattleResponse class with attributes necessary to one participation for one challenger"""

    time_begin = models.DateTimeField()
    time_end = models.DateTimeField()
    battle = models.ForeignKey(Battle,related_name='battles')
    
    def __str__(self):
        return "%s - BattleResponse - User:  %s" % (self.id,self.user)
