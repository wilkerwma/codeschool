import iospec
from cs_core.tests import *
from cs_questions.factories import *
from cs_questions import models


# Register factories
question_io_factory = register(CodingIoQuestionFactory)
question_io = pytest.fixture(lambda db: CodingIoQuestionFactory.create())


@pytest.fixture
def bound_question_io(question_io, user, python, source_hello_py):
    question_io.bind(user=user, language=python, source=source_hello_py)
    return question_io


# Source code fixtures
# We define several fragments of source code in different languages to be used
# in tests.
@pytest.fixture
def iospec_source_hello():
    return CodingIoQuestionFactory.iospec_source


@pytest.fixture
def iospec_hello(iospec_source_hello):
    return iospec.parse_string(iospec_source_hello)


@pytest.fixture
def source_hello_py():
    return CodingIoAnswerKeyFactory.source


@pytest.fixture
def source_hello_c():
    return r'''
#include<stdio.h>

int main() {
    char name[201];
    printf("who? ");
    scanf("%200[^\n]s", name);
    printf("hello %s!", name);
}
'''


# Responses
@pytest.fixture
def valid_response_io(bound_question_io, source_hello_py):
    resp = bound_question_io.register_response_item(source_hello_py)
    resp.autograde()
    return resp