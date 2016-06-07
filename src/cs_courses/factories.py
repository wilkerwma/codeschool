from codeschool.factories import *
from cs_courses.models import Discipline, Course


class DisciplineFactory(factory.DjangoModelFactory):
    class Meta:
        model = Discipline

    name = factory.LazyAttribute(lambda x: fake.word())
    short_description = factory.LazyAttribute(lambda x: fake.sentence())
    long_description = factory.LazyAttribute(lambda x: fake.text())


class CourseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Course

    discipline = factory.SubFactory(DisciplineFactory)
    teacher = factory.SubFactory(UserFactory)
    is_active = True

    @factory.post_generation
    def num_students(self, create, extracted, **kwargs):
        if create and extracted:
            num_students = extracted
            for _ in range(num_students):
                user = UserFactory.create()
                self.register_student(user)


class UserWithCourseFactory(UserFactory):
    course = factory.RelatedFactory(CourseFactory, 'enrolled_courses')
