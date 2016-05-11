import pytest
import factory
from faker import Factory
from pytest_factoryboy import register
from codeschool.fixtures import nodb, saving, use_db
from cs_questions.models import CodingIoQuestion
from codeschool.models import User
fake = Factory.create('pt_BR')


# URL tests
@pytest.mark.django_db
def test_question_owner_urls(coding_io_question, client):
    pk = coding_io_question.pk
    client.force_login(coding_io_question.owner)

    # Detail
    response = client.get('/questions/%s/' % pk)
    assert response.status_code in [200, 301]

    # Update
    response = client.get('/questions/%s/edit/' % pk)
    assert response.status_code in [200, 301]

    # Delete
    response = client.get('/questions/%s/delete/' % pk)
    assert response.status_code in [200, 301]

    # Create
    response = client.get('/questions/new/io/')
    assert response.status_code in [200, 301]


@pytest.mark.django_db
def test_user_urls(coding_io_question, client):
    pk = coding_io_question.pk
    client.force_login(UserFactory.create())

    # Detail
    response = client.get('/questions/%s/' % pk)
    assert response.status_code in [200, 301]

    # Update
    response = client.get('/questions/%s/edit/' % pk)
    assert response.status_code == 404

    # Delete
    response = client.get('/questions/%s/delete/' % pk)
    assert response.status_code == 404

    # Create
    response = client.get('/questions/new/io/')
    assert response.status_code == 404