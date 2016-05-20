from codeschool.testing import *
from cs_core.factories import ProgrammingLanguageFactory
from cs_core.models import get_language
register(ProgrammingLanguageFactory)


def test_get_language_support_most_common_languages(db):
    assert get_language('python').name == 'Python 3.x'
    assert get_language('python2').name == 'Python 2.7'


def test_c_language_aliases(db):
    assert get_language('c') == get_language('gcc')
    assert get_language('cpp') == get_language('g++')
