from codeschool import models


class Address(models.Model):
    city = models.CharField(max_length=200)


class UserProfile(models.Model):
    address = models.ForeignKey(Address, blank=True, null=True)
    gender = models.SmallIntegerField(
        choices=[
            (0, 'male'),
            (1, 'female')
        ],
        blank=True,
        null=True)
    date_of_birth = models.DateField(blank=True, null=True)


class Teacher(models.User):
    profile = models.ForeignKey(UserProfile)


class Student(models.User):
    profile = models.ForeignKey(UserProfile)


@models.User.add_method
def profile_type_name(self):
    """Return the description of the main profile type"""

    if hasattr(self, 'teacher'):
        return 'professor'
    elif hasattr(self, 'student'):
        return 'estudante'
    else:
        return 'usuário'
models.User.profile_type_name = profile_type_name


class SingleUserGroup(models.Group):
    """Represent a group with a single user."""

    owner = models.OneToOneField(models.User)

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


class AllowedUser(models.Model):
    username = models.CharField(primary_key=True, max_length=100)

    @staticmethod
    def register_from_list(data):
        """Register all usernames from the given textual data source. Data
        can be a list of usernames separated by commas or newlines"""

        for username in data.split('\n'):
            user = AllowedUser(username=username)
            user.save()
