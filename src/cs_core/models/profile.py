import datetime
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, ugettext as __
from userena.models import (
    UserenaBaseProfile, UserenaSignup, UserenaBaseProfileManager
)
from codeschool import models
from codeschool import panels
from codeschool.utils import delegate_to
from .sysmodels import profile_root
strptime = datetime.datetime.strptime


class ProfileManager(UserenaBaseProfileManager, models.PageManager):
    """
    Manage objects that are both Wagtail pages and userena profiles.
    """


class Profile(UserenaBaseProfile, models.CodeschoolPage):
    """
    Social information about users.
    """

    class Meta:
       permissions = (
           ('student', _('Can access/modify data visible to student\'s')),
           ('teacher', _('Can access/modify data visible only to Teacher\'s')),
       )

    username = delegate_to('user', True)
    first_name = delegate_to('user')
    last_name = delegate_to('user')
    email = delegate_to('user')

    @property
    def short_description(self):
        return '%s (id: %s)' % (self.get_full_name_or_username(),
                                self.school_id)

    @property
    def age(self):
        if self.date_of_birth is None:
            return None
        today = timezone.now().date()
        return int(round((today - self.date_of_birth).years))

    user = models.OneToOneField(
        models.User,
        unique=True,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_('user'),
        related_name='_profile',
    )
    school_id = models.CharField(
        _('school id'),
        help_text=_('Identification number in your school issued id card.'),
        max_length=50,
        blank=True,
        null=True)
    nickname = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.SmallIntegerField(
        _('gender'),
        choices=[(0, _('male')), (1, _('female'))],
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(
        _('date of birth'),
        blank=True,
        null=True
    )
    website = models.URLField(blank=True, null=True)
    about_me = models.RichTextField(blank=True, null=True)
    objects = ProfileManager.from_queryset(models.PageManager)()

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs and 'id' not in kwargs:
            kwargs.setdefault('parent_page', profile_root())
        super().__init__(*args, **kwargs)

        if self.pk is None and self.user is not None:
            user = self.user
            self.title = self.title or __("%(name)s's profile") % {
                'name': user.get_full_name() or user.username
            }
            self.slug = self.slug or user.username.replace('.', '-')

    def __str__(self):
        if self.user is None:
            return __('Unbound profile')
        full_name = self.user.get_full_name() or self.user.username
        return __('%(name)s\'s profile') % {'name': full_name}

    def get_full_name_or_username(self):
        name = self.user.get_full_name()
        if name:
            return name
        else:
            return self.user.username

    # Wagtail admin
    parent_page_types = ['cs_core.ProfileRoot']
    content_panels = models.CodeschoolPage.content_panels + [
        panels.MultiFieldPanel([
            panels.FieldPanel('school_id'),
        ], heading='Required information'),
        panels.MultiFieldPanel([
            panels.FieldPanel('nickname'),
            panels.FieldPanel('phone'),
            panels.FieldPanel('gender'),
            panels.FieldPanel('date_of_birth'),
        ], heading=_('Personal Info')),
        panels.MultiFieldPanel([
            panels.FieldPanel('website'),
        ], heading=_('Web presence')),
        panels.RichTextFieldPanel('about_me'),
    ]


class FriendshipStatus(models.StatusModel):
    """
    Defines the friendship status between two users.
    """
    STATUS_PENDING = 'pending'
    STATUS_FRIEND = 'friend'
    STATUS_UNFRIEND = 'unfriend'
    STATUS_COLLEAGUE = 'colleague'
    STATUS = models.Choices(
        (STATUS_PENDING, _('pending')),
        (STATUS_FRIEND, _('friend')),
        (STATUS_UNFRIEND, _('unfriend')),
        (STATUS_COLLEAGUE,_('colleague'))
    )
    owner = models.ForeignKey(models.User, related_name='related_users')
    other = models.ForeignKey(models.User, related_name='related_users_as_other')

    class Meta:
        unique_together = ('owner', 'other'),

    def save(self, *args, **kwds):
        super().save(*args, **kwds)

        try:
            FriendshipStatus.objects.get(owner=self.other, other=self.owner)
        except FriendshipStatus.DoesNotExist:
            reciprocal = FriendshipStatus(owner=self.other, other=self.owner)
            if self.status == self.STATUS_COLLEAGUE:
                reciprocal.status = self.STATUS_COLLEAGUE
            else:
                reciprocal.status = self.STATUS_PENDING
            reciprocal.save()
                                

class ExpectedUsername(models.Model):
    """A string of an allowed value for e.g., white listing user names that
    can enroll in a specific course/activity/event etc.

    This class is used to create white lists of users that might not exist yet
    in the database. If you are sure that your users exist, maybe it is more
    convenient to create a regular Group."""

    username = models.CharField(
        max_length=100,
    )
    listener_id = models.IntegerField(
        null=True,
        blank=True,
    )
    listener_type = models.ForeignKey(
        models.ContentType,
        null=True,
        blank=True,
    )
    listener_action = models.CharField(
        max_length=30,
        blank=True,
    )

    @property
    def exists(self):
        return models.User.objects.filter(username=self.username).size() == 1

    @property
    def is_active(self):
        try:
            return models.User.objects.get(username=self.username).is_active
        except models.User.DoesNotExist:
            return False

    @property
    def listener(self):
        ctype = models.ContentType.objects.get(pk=self.listener_type)
        cls = ctype.model_class()
        try:
            return cls.objects.get(pk=self.listener_id)
        except cls.DoesNotExist:
            return None

    @property
    def user(self):
        return models.User.objects.get(username=self.username)

    def notify(self, user=None):
        """
        Notify that user with the given username was created.
        """

        if self.action:
            listener = self.listener
            if listener is not None:
                callback = getattr(listener, action)
                callback(user or self.user)

    def __str__(self):
        return self.username


@receiver(post_save, sender=models.User)
def on_user_save(instance, created, **kwargs):
    """
    Notify that user was just created.
    """

    user = instance
    expected = ExpectedUsername.objects.filter(username=user.username)
    for item in expected:
        item.notify(user)


# We patch the Django's User class by inserting a Mixin into its bases. We only
# add some properties and extend the python-level behavior of the class.
class UserMixin:
    # Delegate profile properties
    about_me = delegate_to('profile')
    date_of_birth = delegate_to('profile')
    gender = delegate_to('profile')
    nickname = delegate_to('profile')
    phone = delegate_to('profile')
    school_id = delegate_to('profile')
    website = delegate_to('profile')
    mugshot = delegate_to('profile')

    @property
    def profile(self):
        try:
            return self._profile
        except Profile.DoesNotExist:
            return Profile.objects.create(user=self)

    @property
    def is_student(self):
        return ...

    @property
    def is_teacher(self):
        return ...

    def _filtered(self, status):
        pks = (
            self.related_users
            .filter(status=status)
            .values_list('other', flat=True)
        )
        return models.User.objects.filter(
            pk__in=pks
        ).order_by('first_name', 'username')

    @property
    def friends(self):
        """A queryset with all the users's friends."""

        return self._filtered('friend')

    @property
    def unfriends(self):
        """A queryset with all users the that were un-friended by the current
        user."""

        return self._filtered('unfriend')

    @property
    def friends_pending(self):
        """A queryset with users that have a pending friendship request
        waiting to be accepted or rejected."""

        return self._filtered('pending')

    def _multi_select(self, field):
        courses = list(self.enrolled_courses.all())
        if not courses:
            return []
        first, *tail = courses
        users = getattr(first, field).all()
        for course in tail:
            users |= getattr(course, field).all()
        users = users.exclude(pk=self.pk)
        return users.order_by('first_name', 'username').distinct()

    @property
    def colleagues(self):
        """A queryset of all user's colleagues."""

        return self._multi_select('students')

    @property
    def staff_contacts(self):
        """A queryset of all staff members to the user's courses."""

        return self._multi_select('staff')

    @property
    def teacher_contacts(self):
        """A queryset of all teachers in the user's enrolled courses."""

        pks = self.enrolled_courses.values_list('teacher', flat=True)
        return models.User.objects.filter(pk__in=pks).distinct()

    def get_absolute_url(self):
        return self.profile.url

models.User.__bases__ = (UserMixin,) + models.User.__bases__
