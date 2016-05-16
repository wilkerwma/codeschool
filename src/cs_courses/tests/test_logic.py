from cs_courses.tests.fixtures import *
from cs_courses.models import Discipline, Course


#
#  Using factory boy
#
register(CourseFactory, 'other_course')


def test_course_metadata(course, discipline):
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
