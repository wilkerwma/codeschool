from codeschool.testing import *
from cs_courses.factories import *
from cs_courses.models import Discipline, Course

#  Fixtures
register(CourseFactory, 'other_course')
register(DisciplineFactory)
register(CourseFactory)


@pytest.mark.django_db
def test_course_metadata(course, discipline):
    assert course.name == discipline.name
    assert course.short_description == discipline.short_description
    assert course.long_description == discipline.long_description


@pytest.mark.django_db
def test_students_are_colleagues(course_factory, discipline):
    course = course_factory.create(num_students=3)
    s1, s2, s3 = course.students.all()
    assert len(s1.colleagues) == 2
    assert s2 in s1.colleagues
    assert s3 in s1.colleagues
    assert s1 not in s1.colleagues
