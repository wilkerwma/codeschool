from django.db import models
from cs_activities.models import Activity, Response
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from codeschool import models
from codeschool.models import User
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Response)
def my_handler(sender, **kwargs):
    print(sender, kwargs)


class HasCategoryMixin:
	CATEGORY_TRIED = 'tried'
	CATEGORY_INCOMPLETE = 'incomplete'
	CATEGORY_CORRECT = 'correct'
	CATEGORY_CHOICES = [
		(CATEGORY_TRIED, _('tried')),
		(CATEGORY_INCOMPLETE, _('incomplete')),
		(CATEGORY_CORRECT, _('correct'))
	]
	category = models.CharField(choices=CATEGORY_CHOICES)


#É UMA RESPONSE DA CLASSE Activity
class Action(models.Model):
	points_tried = models.PositiveIntegerField(default=0)
	points_incomplete = models.PositiveIntegerField(default=5)
	points_correct = models.PositiveIntegerField(default=10)
	activity = models.ForeignKey(Activity)



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
	required_points = models.PositiveIntegerField(default=0)
	required_actions = models.ManyToManyField(Action)

class GoalStep(HasCategoryMixin, models.Model):
	goal = models.ForeignKey(Goal, related_name='steps')
	action = models.ForeignKey(Action)
	category = models.CharField(choices=HasCategoryMixin.CATEGORY_CHOICES, null=True, blank=True, max_length=20)

class PblUser(models.Model):
	users = models.OneToOneField(models.User)
	accumulated_points = models.PositiveIntegerField()


class GivenPoints(HasCategoryMixin, models.TimeStampedModel):
	action = models.ForeignKey(Action)
	users = models.ForeignKey(PblUser)

	def value(self):
		if self.category == self.CATEGORY_CORRECT:
			return self.action.points_correct
		elif self.category == self.CATEGORY_INCOMPLETE:
			return self.action.points_incomplete
		elif self.category == self.CATEGORY_TRIED:
			return self.action.points_tried
		else:
			raise ValueError('invalid category: %s' % self.category)

	def __int__(self):
		return self.value()
