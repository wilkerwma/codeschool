from django.db import models
from cs_activities.models import Activity
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from codeschool import models
from codeschool.models import User
from django.contrib.auth.models import User

#É UMA RESPONSE DA CLASSE Activity
class Action(models.Model):
	points = models.PositiveIntegerField()
	activity = models.ForeignKey(Activity)
	user = models.ForeignKey(models.User)


class Badge(models.Model):
	name = models.CharField(_('name'), max_length=200)
	image = models.ImageField(upload_to = 'static/badge', default = '/static/badge/none.jpg')
	short_description = models.TextField(_('short description'))
	long_description = models.TextField(_('long description'), blank=True)

class GivenBadge(models.TimeStampedModel):
	badge = models.ForeignKey(Badge)
	users = models.ForeignKey(models.User)

class Goal(models.Model):

	badge = models.ForeignKey(
		Badge,
		related_name='goals'
	)

	activities = models.ForeignKey(
        Activity,
        related_name='goals',
    )
