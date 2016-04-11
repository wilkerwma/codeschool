import datetime
from codeschool import models
from django.contrib.auth.models import Group, AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser
from model_utils.managers import QueryManagerMixin
from address.models import AddressField
from userena.models import UserenaBaseProfile


strptime = datetime.datetime.strptime


class Profile(UserenaBaseProfile):
    """
    Userena profile.

    Social information about our users.
    """
    user = models.OneToOneField(
        models.User,
        unique=True,
        verbose_name=_('user'),
        related_name=_('profile'),
    )
    nickname = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = AddressField(blank=True, null=True)
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
    about_me = models.TextField(blank=True, null=True)

    @property
    def age(self):
        today = datetime.now().date()
        return int(round((today - self.date_of_birth).days / 365.25))

    def custom_fields(self, flat=False):
        """Return a dictionary with all custom fields"""

        D = {}
        for value in self.custom_field_values.all():
            category = value.category_name
            field_name = value.field_name
            data = value.data
            if flat:
                D[(category, field_name)] = data
            else:
                category_dict = D.setdefault(category, {})
                category_dict[field_name] = data

        return D

    class Meta:
        permissions = (
            ('student', _('Can access/modify data visible to student\'s')),
            ('teacher', _('Can access/modify data visible only to Teacher\'s')),
        )

    def __getattr__(self, attr):
        return getattr(self.user, attr)


class CustomFieldCategory(models.Model):
    """
    A category for custom site-wide fields.
    """
    ref = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=140)
    description = models.TextField()


class CustomFieldDefinition(models.Model):
    """
    Define a custom site-specific field for the user profile.
    """
    name = models.CharField(max_length=140)
    description = models.TextField()
    category = models.ForeignKey(CustomFieldCategory)
    required = models.BooleanField(default=False)
    required_permissions = models.ManyToManyField(models.Permission)
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


class FriendshipStatus(models.StatusModel):
    STATUS = models.Choices(
        ('pending', _('pending')),
        ('friend', _('friend')),
        ('colleague', _('colleague')),
        ('unfriend', _('unfriend'))
    )

    self = models.ForeignKey(models.User, related_name='associated')
    other = models.ForeignKey(models.User, related_name='associated_as_other')

    class Meta:
        unique_together = ('self', 'other'),

    def save(self, *args, **kwds):
        super().save(*args, **kwds)

        try:
            FriendshipStatus.objects.get(self=self.other, other=self.self)
        except FriendshipStatus.DoesNotExist:
            FriendshipStatus(
                    self=self.other,
                    other=self.self,
                    status='pending').save()



# Mokey patch the user class

class UserMixin:
    @property
    def is_student(self):
        return ...

    @property
    def is_teacher(self):
        return ...

    @property
    def is_person(self):
        return hasattr(self, 'person')

    @property
    def friends(self):
        return self.associated.filter(status='friend')

    @property
    def unfriends(self):
        return self.associated.filter(status='unfriend')

    @property
    def colleagues(self):
        return self.associated.filter(status='colleague')

    @property
    def friends_pending(self):
        return self.associated_as_other.filter(status='pending')

models.User.__bases__ = (UserMixin,) + models.User.__bases__