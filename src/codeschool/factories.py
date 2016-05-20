"""
Factories used for populating database both in tests or demos.
"""

import factory
from faker import Factory as FakerFactory
from codeschool.models import User

__all__ = ['fake', 'UserFactory', 'create_users', 'factory']

# Fake factory -- use this to create fake data (e.g. fake.name())
fake = FakerFactory.create()


# Factory boy factories
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.LazyAttribute(lambda x: fake.first_name())
    last_name = factory.LazyAttribute(lambda x: fake.last_name())
    username = factory.LazyAttribute(lambda x: fake.user_name())
    email = factory.LazyAttribute(lambda x: fake.email())


def create_users(N=10):
    """Return a list with N new users.

    This might be useful when populating database for a demo site or during
    testing."""

    return [UserFactory.create() for _ in range(N)]

