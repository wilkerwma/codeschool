from decimal import Decimal
from django.utils.translation import ugettext_lazy as _
from codeschool import models
from cs_core.models import ProgrammingLanguage
from cs_activities.models import Activity, Response
from cs_questions.models.base import Question, QuestionResponse
from cs_questions.models.numeric import NumericResponse
from cs_questions.models.coding_io import CodingIoResponseItem


class QuizActivityItem(models.ListItemModel):
    """
    A question in a quiz.
    """

    class Meta:
        root_field = 'quiz'

    quiz = models.ForeignKey('QuizActivity')
    question = models.ForeignKey(Question)


class QuizActivity(Activity):
    """
    Represent a quiz.
    """

    class Meta:
        verbose_name = _('quiz activity')
        verbose_name_plural = _('quiz activities')

    GRADING_METHOD_MAX = 0
    GRADING_METHOD_MIN = 1
    GRADING_METHOD_AVERAGE = 2
    GRADING_METHOD_CHOICES = (
        (GRADING_METHOD_MAX,  _('largest grade of all responses')),
        (GRADING_METHOD_MIN,  _('smallest grade of all responses')),
        (GRADING_METHOD_AVERAGE,  _('mean grade')),
    )
    quiz_grading_method = models.IntegerField(
        choices=GRADING_METHOD_CHOICES
    )
    language = models.ForeignKey(ProgrammingLanguage, blank=True, null=True)

    # Derived attributes
    items = QuizActivityItem.as_items()
    questions = property(lambda x: list(x))
    num_questions = property(lambda x: len(x.items))

    def __iter__(self):
        return (x.question.as_subclass() for x in self.items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx].question

    def __delitem__(self, idx):
        del self.items[idx]

    def add_question(self, question):
        """Add a question to the quiz."""

        item = QuizActivityItem(quiz=self, question=question)
        item.save()
        self.items.append(item)

    def get_user_response(self, user):
        """Return a response object for the given user.

        For now, users can only have one response ."""

        try:
            response = self.responses.filter(user=user, parent__isnull=True).first()
            if response:
                return response.quizresponse
            else:
                raise Response.DoesNotExist
        except Response.DoesNotExist:
            new = QuizResponse.objects.create(activity=self, user=user)
            return new

    def register_response(self, user, response, commit=True):
        """Register a question response to the given user."""

        self.get_user_response(user).register_response(response, commit)

    def iter_tagged_questions(self, tag='answered', user=None):
        """Iterate over tuples of (question, question) where tag is some property
        associated with each question.

        Args:
            tag:
                Some property pertaining to the question. It accept the
                following string values:

                answered:
                    A boolean value telling if the question has been answered
                    by the user.
            user:
                The user associated with the tag. This may be necessary to
                some tags.
        """

        if tag == 'answered':
            response = self.get_user_response(user)
            for question in self.questions:
                yield (question, response.is_answered(question))
        else:
            return NotImplemented

    def get_final_grade(self, user):
        """Return the final grade for the given user."""

        response = self.get_user_response(user)
        return response.get_final_grade()

    #def select_responses(self):
    #    return super().select_responses().filter(parent__isnull=True)


class QuizResponse(Response):
    """
    A response to a quiz activity.

    This object coordinate all responses for the questions registered in the
    quiz.
    """

    num_questions = property(lambda x: x.quiz.num_questions)

    @property
    def quiz(self):
        return self.activity.quizactivity

    def register_response(self, response, commit=True):
        """
        Register a question response to itself.
        """

        assert isinstance(response, QuestionResponse), response
        response.parent = self
        response.activity = self.activity
        if commit:
            response.save()

    def is_answered(self, question):
        """
        Return True if question has been answered in the quiz.
        """

        # TODO: make QuestionResponse concrete
        return (
            bool(CodingIoResponseItem.objects.filter(
                parent=self,
                question_for_unbound=question
            )) or
            bool(NumericResponse.objects.filter(
                parent=self,
                question_for_unbound=question
            ))
        )

    def autograde_compute(self):
        grades = []
        print('regrading', self.user.username)

        for question in self.quiz.questions:
            responses = set(CodingIoResponseItem.objects.filter(
                parent=self, question_for_unbound=question
            ).values_list('id', flat=True))
            responses |= set(NumericResponse.objects.filter(
                parent=self, question_for_unbound=question
            ).values_list('id', flat=True))

            responses = Response.objects.filter(id__in=responses)
            if responses:
                grade = max(responses.values_list('final_grade', flat=True))
                grades.append(grade)
            else:
                grades.append(Decimal(0))

        if grades:
            print(grades)
            min_grade = min(grades)
            del grades[grades.index(min_grade)]

            grade = sum(grades) / (self.num_questions - 1)
            print(grade, self.num_questions, self.status)
            return grade
        return Decimal(0)

    def get_final_grade(self):
        """
        Compute the final grade for the quiz activity.
        """

        if self.final_grade != None:
            return self.final_grade
        return 0
