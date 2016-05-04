import pytest
import factory
from pytest_factoryboy import register
from codeschool.testing import user, nodb, fake, faker, saving
from cs_courses.models import Discipline, Course


@pytest.fixture
def use_db():
    return False


# Simple fixtures
@pytest.fixture
def discipline_fixture(fake, use_db):
    return saving(Discipline(
        name=fake.word(),
        short_description=fake.sentence(),
        long_description=fake.text(),
    ), use_db)


@pytest.fixture
def course_fixture(fake, discipline_fixture, user, use_db):
    return saving(Course(
        discipline=discipline_fixture,
        teacher=user,
        is_active=True,
    ), use_db)


def test_course_metadata(course_fixture, discipline_fixture):
    course, discipline = course_fixture, discipline_fixture
    assert course.name == discipline.name
    assert course.short_description == discipline.short_description
    assert course.long_description == discipline.long_description


#
#  Using factory boy
#
@register
class DisciplineFactory(factory.Factory):
    class Meta:
        model = Discipline

    name = 'test discipline'
    short_description = faker.sentence()
    long_description = faker.text()


@register
class CourseFactory(factory.Factory):
    class Meta:
        model = Course

    discipline = factory.SubFactory(DisciplineFactory)
    teacher = user(faker, use_db())
    is_active = True


register(CourseFactory, 'other_course', teacher=user(faker, use_db()))


def test_course_metadata_factory_boy(course, discipline):
    assert course.name == discipline.name
    assert course.short_description == discipline.short_description
    assert course.long_description == discipline.long_description


def test_other_course(course, other_course):
    assert other_course.name == 'test discipline'
    assert other_course.teacher != course.teacher


def test_course_factory(course_factory):
    course = course_factory(is_active=False)
    assert course.is_active == False
    assert course.name == 'test discipline'
