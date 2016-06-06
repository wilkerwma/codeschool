from django.forms import ModelForm
from cs_battles.models import BattleResponse

class BattleForm(ModelForm):
    class Meta:
        model = BattleResponse
        fields = ['source']
