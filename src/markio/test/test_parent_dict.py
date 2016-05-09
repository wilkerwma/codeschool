import pytest
from markio.types import pdict


def test_parent_dict():
    parent = {'baz': 'spam'}
    d = pdict(parent, foo='bar')
    assert 'baz' in d
    assert len(d) == 2
    assert set(d) == {'baz', 'foo'}
