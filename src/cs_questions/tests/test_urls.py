import pytest
import pytest_django
from codeschool.testing import use_db
from cs_questions.tests.test_logic import question as question_io


@pytest.mark.django_db
def test_io_questions_crud_urls(question_io, client):
    pk = question_io.pk

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
