from django.core.exceptions import ValidationError
from cs_core.factories import ProgrammingLanguageFactory
from codeschool.tests import *
from cs_core import models
from cs_core.tests import *


#
# Test system models
#
def test_sys_model_constructors_return_valid_instances(db):
    rogue = models.rogue_root()
    hidden = models.hidden_root()
    profile = models.profile_root()
    for model in [hidden, profile, rogue]:
        assert isinstance(model, models.Page)
        assert model.pk is not None

#
# Test file formats
#
def test_get_language_support_most_common_languages(db):
    assert models.programming_language('python').name == 'Python 3.5'
    assert models.programming_language('python2').name == 'Python 2.7'


def test_c_language_aliases(db):
    lang = models.programming_language
    assert lang('c') == lang('gcc')
    assert lang('cpp') == lang('g++')


def test_new_unsupported_language(db):
    # Explicit mode
    with pytest.raises(models.ProgrammingLanguage.DoesNotExist):
        models.programming_language('foolang')

    # Silent mode
    lang = models.programming_language('foolang', raises=False)
    assert lang.ref == 'foolang'
    assert lang.name == 'Foolang'
    assert lang.is_supported is False
    assert lang.is_language is True
    assert lang.is_binary is False


#
# Tests user profile
#
def test_user_profile_is_created_automatically(db, user):
    user = models.User(username='foo')
    user.save()
    assert hasattr(user, 'profile')


def test_use_access_profile_attributes(db, user_with_profile):
    user, profile = user_with_profile
    assert user.about_me == profile.about_me