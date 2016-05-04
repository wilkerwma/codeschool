"""
Functions that aids writing unit tests.
"""

import pytest
from faker import Factory as FakerFactory
from codeschool.db import use_db as _use_db, nodb, saving as saving
from codeschool.models import User
faker = FakerFactory.create()


# Faker support
@pytest.fixture(scope='module')
def faker_locale():
    return 'pt_BR'


@pytest.fixture(scope='module')
def fake(faker_locale):
    return FakerFactory.create(faker_locale)


# Should we touch the database?
@pytest.fixture
def use_db():
    return _use_db()


@pytest.fixture
def user(fake, use_db):
    user = User(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        username=fake.user_name(),
        email=fake.email(),
    )
    user.set_password(fake.password())

    return saving(user, use_db)


