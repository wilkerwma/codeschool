import datetime
from codeschool import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, ugettext as __
from userena.models import UserenaBaseProfile, UserenaSignup


strptime = datetime.datetime.strptime


# class Profile(UserenaBaseProfile):
#     """
#     Userena profile.
#
#     Social information about our users.
#     """
#     user = models.OneToOneField(
#         models.User,
#         unique=True,
#         verbose_name=_('user'),
#         related_name='profile_userena',
#     )
#     school_id = models.CharField(
#         _('school id'),
#         help_text=_('Identification number in your school issued id card.'),
#         max_length=50,
#         blank=True,
#         null=True)
#     nickname = models.CharField(max_length=50, blank=True, null=True)
#     phone = models.CharField(max_length=20, blank=True, null=True)
#     gender = models.SmallIntegerField(
#         _('gender'),
#         choices=[(0, _('male')), (1, _('female'))],
#         blank=True,
#         null=True
#     )
#     date_of_birth = models.DateField(
#         _('date of birth'),
#         blank=True,
#         null=True
#     )
#     website = models.URLField(blank=True, null=True)
#     about_me = models.TextField(blank=True, null=True)
#
#     @property
#     def age(self):
#         if self.date_of_birth is None:
#             return None
#         today = timezone.now().date()
#         return int(round((today - self.date_of_birth).days / 365.25))
#
#     @property
#     def contact_classes(self):
#         user = self.user
#
#         try:
#             friends = user.friends
#             colleagues = user.staff_contacts
#             staff = user.colleagues
#         except AttributeError as ex:
#             raise RuntimeError(ex)
#
#         return [friends, colleagues, staff]
#
#     def custom_fields(self, flat=False):
#         """Return a dictionary with all custom fields"""
#
#         D = {}
#         for value in self.custom_field_values.all():
#             category = value.category_name
#             field_name = value.field_name
#             data = value.data
#             if flat:
#                 D[(category, field_name)] = data
#             else:
#                 category_dict = D.setdefault(category, {})
#                 category_dict[field_name] = data
#
#         return D
#
#     class Meta:
#        permissions = (
#            ('student', _('Can access/modify data visible to student\'s')),
#            ('teacher', _('Can access/modify data visible only to Teacher\'s')),
#        )
#
#     def __str__(self):
#         if self.user is None:
#             return __('unbound profile')
#         return __('%(name)s\'s profile') % {'name': self.user.get_full_name()}
#
#     def __repr__(self):
#         return str(self.contact_classes)
from cs_core.models import Profile


class CustomFieldCategory(models.Model):
    """
    A category for custom site-wide fields.
    """
    name = models.CharField(max_length=40)
    description = models.CharField(max_length=140)


class CustomFieldDefinition(models.Model):
    """
    Define a custom site-specific field for the user profile.
    """
    name = models.CharField(max_length=40)
    description = models.CharField(max_length=140)
    category = models.ForeignKey(CustomFieldCategory)
    enabled = models.BooleanField(
        _('enabled'),
        help_text=_('Enable or disable a custom field'),
        default=True,
    )
    type = models.CharField(
        default='text',
        blank=True,
        max_length=10,
        choices=[
            ('text', _('text')),
            ('int', _('int')),
            ('float', _('float')),
            ('date', _('date')),
            ('datetime', _('datetime'))
        ])

    from_db_conversions = {
        'text': lambda x: x,
        'int': int,
        'float': float,
        'date': lambda x: datetime.date(*map(int, x.split('-'))),
        'datetime': lambda x: strptime("%Y-%m-%dT%H:%M:%S.%f%z", x),
    }

    to_db_conversions = {
        'date': lambda x: x.isoformat(),
        'datetime': lambda x: x.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
    }


class CustomFieldValue(models.Model):
    """
    Represents a value of a custom field.

    Since custom fields can have many different types, we store all of them
    as a TextField and provide serializers for each type in order to convert
    each field to the correct type. The ``value`` attribute is always converted
    to the correct type.
    """

    definition = models.ForeignKey(CustomFieldDefinition)
    profile = models.ForeignKey(Profile, related_name='custom_field_values')
    db_value = models.TextField()

    @property
    def value(self):
        tt = self.definition.type
        if tt == 'text':
            return self.db_value
        elif tt == 'float':
            return float(self.db_value)


class SingleUserGroup(models.Group):
    """Represent a group with a single user.

    Theses groups are useful to be plugged to models that could accept either
    a group or a single user reference."""

    owner = models.OneToOneField(models.User, related_name='owned_group')

    def save(self, *args, **kwds):
        self.name = 'single-group-%s' % self.owner.username
        if not self.pk:
            super().save()
        self.user_set.add(self.owner)
        super().save(*args, **kwds)

    @classmethod
    def from_user(cls, user):
        """Return an existing single-user group for user or create a new one
        if it does not exist"""

        try:
            return cls.objects.get(owner=user)
        except cls.DoesNotExist:
            group = cls(owner=user)
            group.save()
            return group


class AllowedUsername(models.Model):
    """A string of an allowed value for e.g., white listing user names that
    can enroll in a specific course/activity/event etc.

    This class is used to create whitelists of users that might not exist yet in
    the database. If you are sure that your users exist, maybe it is more
    convenient to create a regular Group."""

    username = models.CharField(primary_key=True, max_length=100)

    @property
    def exists(self):
        return models.User.objects.filter(username=self.username).size() == 1

    @property
    def is_active(self):
        try:
            return models.User.objects.get(username=self.username).is_active
        except models.User.DoesNotExist:
            return False

    def __str__(self):
        return self.username


class AllowedUsernameListing(models.Model):
    """A listing of allowed usernames"""

    name = models.CharField(primary_key=True, max_length=100)
    usernames = models.ManyToManyField(AllowedUsername)

    @classmethod
    def from_data(cls, name, data):
        """Register all usernames from the given textual data source. Data
        can be a list of usernames separated by commas, spaces or newlines"""

        date = data.replace(',', '\n')
        return cls.from_list(name, date.split())

    @classmethod
    def from_list(cs, name, lst):
        """Similar to from_data(), but expect a sequence of strings."""

        listing = AllowedUsernameListing.objects.create(name)

        for username in lst:
            user = AllowedUsername.objects.create(username=str(username))
            listing.usernames.add(user)
        listing.save()


# class _FriendshipStatus(models.StatusModel):
#     """
#     Defines the friendship status between two users.
#     """
#     STATUS_PENDING = 'pending'
#     STATUS_FRIEND = 'friend'
#     STATUS_UNFRIEND = 'unfriend'
#     STATUS_COLLEAGUE = 'colleague'
#     STATUS = models.Choices(
#         (STATUS_PENDING, _('pending')),
#         (STATUS_FRIEND, _('friend')),
#         (STATUS_UNFRIEND, _('unfriend')),
#         (STATUS_COLLEAGUE,_('colleague'))
#     )
#     owner = models.ForeignKey(models.User, related_name='related_users')
#     other = models.ForeignKey(models.User, related_name='related_users_as_other')
#
#     class Meta:
#         unique_together = ('owner', 'other'),
#
#     def save(self, *args, **kwds):
#         super().save(*args, **kwds)
#
#         try:
#             FriendshipStatus.objects.get(owner=self.other, other=self.owner)
#         except FriendshipStatus.DoesNotExist:
#             reciprocal = FriendshipStatus(owner=self.other, other=self.owner)
#             if self.status == self.STATUS_COLLEAGUE:
#                 reciprocal.status = self.STATUS_COLLEAGUE
#             else:
#                 reciprocal.status = self.STATUS_PENDING
#             reciprocal.save()
# FriendshipStatus = _FriendshipStatus
from cs_core.models import FriendshipStatus


class UserMixin:
    """
    Mokey-patch the user class with some additional methods and attributes.
    """
    @property
    def is_student(self):
        return ...

    @property
    def is_teacher(self):
        return ...

    @property
    def is_person(self):
        return hasattr(self, 'profile')

    def _filtered(self, status):
        pks = (
            self.related_users
            .filter(status=status)
            .values_list('other', flat=True)
        )
        return models.User.objects.filter(pk__in=pks).order_by('first_name', 'username')

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


models.User.__bases__ = (UserMixin,) + models.User.__bases__
