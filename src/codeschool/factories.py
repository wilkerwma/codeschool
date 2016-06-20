import factory
from factory import *
from faker import Factory as FakerFactory
from codeschool import models as _models


# Fake factory -- use this to create fake data (e.g. fake.name())
fake = FakerFactory.create()


#
# User factories
#
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = _models.User

    first_name = factory.LazyAttribute(lambda x: fake.first_name())
    last_name = factory.LazyAttribute(lambda x: fake.last_name())
    username = factory.LazyAttribute(lambda x: fake.user_name())
    email = factory.LazyAttribute(lambda x: fake.email())


def create_users(N=10):
    """
    Return a list with N new users.

    This might be useful when populating database for a demo site or during
    testing.
    """

    return [UserFactory.create() for _ in range(N)]


# We now create an alias to all fake methods in the form of fake_name()
# These will create LazyAttribute instances that call the correct fake method.
def _fake_lazy_attribute_factory(fake_method_name):
    fake_method = getattr(fake, fake_method_name)

    def attribute_func(*args, **kwargs):
        return factory.LazyAttribute(lambda x: fake_method(*args, **kwargs))

    attribute_func.__name__ = 'fake_' + fake_method_name
    attribute_func.__doc__ = fake_method.__doc__

    return attribute_func

for _name in dir(fake):
    if not _name.startswith('_'):
        globals()['fake_' + _name] = _fake_lazy_attribute_factory(_name)