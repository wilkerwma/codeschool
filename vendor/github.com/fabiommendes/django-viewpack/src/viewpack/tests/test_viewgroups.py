import pytest
import pytest_django
from viewpack import ViewPack, View
from test_app import models
from test_app import views


def test_viewgroup_metainfo():
    view = views.TestViewPack
    assert set(view._meta.view_attributes) == {'detail', 'edit'}


def test_view_group_create_mixins():
    class Mixin:
        pass

    class A(ViewPack):
        class V(View):
            pass

    class B(A):
        VMixin = Mixin

    assert not hasattr(B, 'VMixin')
    assert B.V is not A.V
    assert issubclass(B.V, A.V)


@pytest.yield_fixture
def obj():
    new = models.TestModel.objects.create(name='name', description='description')
    yield new
    new.delete()


@pytest.mark.django_db
def test_crud_urls(client, obj):
    response = client.get('/crud/%s/' % obj.pk)

    # Is it the right data?
    lines = response.content.decode('utf8').splitlines()
    lines = [line.strip() for line in lines]
    assert lines == [
        '<h1>Test Model: name</h1>',
        '<h2>Description</h2>',
        '<div>description</div>'
    ]

    # Assert status codes
    assert response.status_code in [200, 301]
    assert client.get('/crud/').status_code == 200
    assert client.get('/crud/new').status_code in [200, 301]
    assert client.get('/crud/%s/edit' % obj.pk).status_code in [200, 301]
    assert client.get('/crud/%s/delete' % obj.pk).status_code in [200, 301]


if __name__ == '__main__':
    pytest.main()