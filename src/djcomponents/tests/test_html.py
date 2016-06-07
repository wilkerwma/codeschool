import pytest
from djcomponents import *
from djcomponents import core
core.DEBUG = False


def test_list_element():
    ls = List([1, 2], classes='foo')
    assert ls.render() == '<ul class="foo"><li>1</li><li>2</li></ul>'


def test_tag_with_attributes():
    assert Div(id="bar", classes="foo").render() == '<div class="foo" id="bar"></div>'


def test_tag_a():
    a = Anchor(href="foo", link_name="bar")
    assert a.attrs == {'href': 'foo'}
    assert a.href == "foo"
    assert a.render() == '<a href="foo">bar</a>'


def test_tag_accessor():
    widget = tag.ul([
        tag.a(href="beatle/%s/" % name, link_name=name.title())
        for name in ['john', 'paul', 'george', 'ringo']
    ])
    assert widget.render() == (
        '<ul>'
        '<li><a href="beatle/john/">John</a></li>'
        '<li><a href="beatle/paul/">Paul</a></li>'
        '<li><a href="beatle/george/">George</a></li>'
        '<li><a href="beatle/ringo/">Ringo</a></li>'
        '</ul>'
    )
