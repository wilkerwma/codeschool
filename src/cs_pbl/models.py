from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from codeschool import models
from codeschool.utils import delegate_to
from cs_core.models import Activity, autograde_signal


@receiver(autograde_signal)
def register_pbl_response(given_grade, response_item, **kwargs):

    try:
        pbl_user = response_item.user.pbl_user
    except PblUser.DoesNotExist:
        pbl_user = PblUser.objects.create(user=response_item.user)

    category = category_from_response(response_item)

    activity = response_item.activity
    actions = Action.objects.filter(activity=activity)

    previous_points = pbl_user.accumulated_points

    for action in actions:
        register_points(pbl_user, action, category)

    if previous_points < pbl_user.accumulated_points:
        register_point_badge(previous_points, pbl_user)

    # response_item.response grupo de reponse itens do mesmo usuário e da mesma atividade
    # response.itens é o manager do django.

def category_from_response(response_item):
    if response_item.status == response_item.STATUS_INCOMPLETE:
        return GivenPoints.CATEGORY_INCOMPLETE
    elif response_item.status != response_item.STATUS_DONE:
        return GivenPoints.CATEGORY_TRIED
    else:
        if response_item.given_grade < 100:
            return GivenPoints.CATEGORY_TRIED
        elif response_item.response.items.count() == 1:
            return GivenPoints.CATEGORY_CORRECT_AT_FIRST_TRY
        else:
            return GivenPoints.CATEGORY_CORRECT

def register_points(user, action, category):
    given_points, created = GivenPoints.objects.get_or_create(user=user, action=action)

    given_points.update(category)

def register_point_badge(previous_points, pbl_user):
        '''
        point_badges = PointBadge.objects.filter(
            required_points__gt=previous_points
        ).filter(
            required_points__lte=pbl_user.accumulated_points
        )
        '''

        point_badges = PointBadge.objects.filter()

        for point_badge in point_badges:
            if point_badge.required_points <= pbl_user.accumulated_points:
                GivenBadge.objects.get_or_create(badge=point_badge, user=pbl_user)

class HasCategoryMixin:
    CATEGORY_TRIED = 'tried'
    CATEGORY_INCOMPLETE = 'incomplete'
    CATEGORY_CORRECT = 'correct'
    CATEGORY_CORRECT_AT_FIRST_TRY = 'correct_at_first_try'
    CATEGORY_CHOICES = [
        (CATEGORY_TRIED, _('tried')),
        (CATEGORY_INCOMPLETE, _('incomplete')),
        (CATEGORY_CORRECT, _('correct')),
        (CATEGORY_CORRECT_AT_FIRST_TRY, _('correct_at_first_try'))
    ]
    category = models.CharField(choices=CATEGORY_CHOICES)

class Action(models.Model):
    points_tried = models.PositiveIntegerField(default=5)
    points_incomplete = models.PositiveIntegerField(default=0)
    points_correct = models.PositiveIntegerField(default=10)
    points_correct_at_first_try = models.PositiveIntegerField(default=12)
    activity = models.ForeignKey(models.Page)
    name = models.CharField(_('name'), default="Action", max_length=200)
    short_description = delegate_to('activity')
    long_description = delegate_to('activity')


    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)
        #if self.activity is not None:
    #    if self.activity is None:
    #        self.activity = self.activity.specific

    def clean(self):
        super().clean()
        self.activity = self.activity.specific
        if not isinstance(self.activity, Activity):
            raise ValidationError({'activity': _('Page is not an activity!')})

    class Meta():
        verbose_name = _('action')
        verbose_name_plural = _('actions')

    title = property(lambda x: x.name)

    def __str__(self):
        return self.name

class BaseBadge(models.PolymorphicModel):
    name = models.CharField(_('name'), max_length=200)
    image = models.ImageField(upload_to = 'static/badge', default = '/static/badge/none.png')
    short_description = models.TextField(_('short description'))
    long_description = models.TextField(_('long description'), blank=True)

    def get_absolute_url(self):
        return  reverse('/detail')

    def __str__(self):
        return self.name

class PointBadge(BaseBadge):
    required_points = models.IntegerField(default=0)

class GoalStep(HasCategoryMixin, models.Model):
    point_badge = models.ForeignKey(PointBadge, null=True)
    action = models.ForeignKey(Action)
    category = models.CharField(choices=HasCategoryMixin.CATEGORY_CHOICES, null=True, blank=True, max_length=20)
    required = models.BooleanField()



class PblUser(models.Model):
    user = models.OneToOneField(models.User, related_name='pbl_user')
    accumulated_points = models.PositiveIntegerField(default=0)
    username = delegate_to('user')
    first_name = delegate_to('user')
    last_name = delegate_to('user')
    get_full_name = delegate_to('user')

class GivenPoints(HasCategoryMixin, models.TimeStampedModel):
    action = models.ForeignKey(Action)
    user = models.ForeignKey(PblUser)
    points = models.IntegerField(default=0)

    def __int__(self):
        return self.value()

    def value(self, category):
        if category == self.CATEGORY_CORRECT:
            return self.action.points_correct
        elif category == self.CATEGORY_INCOMPLETE:
            return self.action.points_incomplete
        elif category == self.CATEGORY_TRIED:
            return self.action.points_tried
        elif category == self.CATEGORY_CORRECT_AT_FIRST_TRY:
            return self.action.points_correct_at_first_try
        else:
            raise ValueError('invalid category: %s' % category)

    def update(self, category):
        value = self.value(category)
        if value >= self.points:
            pbl_user = self.user
            pbl_user.accumulated_points += value - self.points
            pbl_user.save()
            self.points = value
            self.save()

class GivenBadge(models.TimeStampedModel):
    class Meta:
        unique_together = [['badge','user']]

    badge = models.ForeignKey(BaseBadge)
    user = models.ForeignKey(PblUser, null='True')

    name = delegate_to('basebadge')
    short_description = delegate_to('basebadge')
    long_description = delegate_to('basebadge')
