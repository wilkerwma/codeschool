from codeschool import models


class QuestionPage(models.CodeschoolPage):
    """
    A page that displays a list of all questions registered in this course.
    """

    def add_question(self, question, copy=True):
        """
        Register a new question to the course.

        If `copy=True` (default), register a copy.
        """

        if copy:
            question = question.copy()
        question.move(self)
        question.save()

    def new_question(self, cls, *args, **kwargs):
        """
        Create a new question instance by calling the cls with the given
        arguments and add it to the course.
        """

        kwargs['parent_node'] = self
        return cls.objects.create(*args, **kwargs)