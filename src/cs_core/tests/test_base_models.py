from codeschool.tests import *
from cs_core.factories import ProgrammingLanguageFactory
from cs_core.models import get_language, ProgrammingLanguage


def test_get_language_support_most_common_languages(db):
    assert get_language('python').name == 'Python 3.5'
    assert get_language('python2').name == 'Python 2.7'


def test_c_language_aliases(db):
    assert get_language('c') == get_language('gcc')
    assert get_language('cpp') == get_language('g++')


def test_new_unsupported_language(db):
    lang = ProgrammingLanguage.get_language('foolang')
    assert lang.ref == 'foolang'
    assert lang.name == 'Foolang'
    assert lang.is_supported is False
    assert lang.is_language is True
    assert lang.is_binary is False