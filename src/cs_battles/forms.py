from django.forms import ModelForm
from cs_ranking.models import Battle

class BattleInvitationForm(ModelForm):
    class Meta:
        model = Battle
        fields = ['question', 'language']

class BattleForm(ModelForm):
    class Meta:
        model = Battle
        fields = ['battle_code']
