import pytest
from codeschool.tests import *
from cs_core.factories import *
from cs_core import models
from cs_core.models import programming_language


@pytest.fixture
def user_with_profile():
    user = factory.UserFactory.create()
    user.profile.school_id = '12345'
    user.profile.gender = 'male'
    user.profile.about_me = 'i am ok'
    return (user, user.profile)


# Programming language fixtures
python = pytest.fixture(lambda: programming_language('python'))
c = pytest.fixture(lambda: programming_language('c'))
cpp = pytest.fixture(lambda: programming_language('cpp'))
ruby = pytest.fixture(lambda: programming_language('ruby'))
