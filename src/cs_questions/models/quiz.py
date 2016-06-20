from decimal import Decimal
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from codeschool import models
from codeschool import panels
from cs_core.models import ProgrammingLanguage, Activity, Response
from cs_questions.models import Question, QUESTION_STEM_BLOCKS


class QuizItem(models.MigrateMixin, models.Orderable):
    """
    A question in a quiz.
    """

    quiz = models.ParentalKey(
        'cs_questions.Quiz',
        related_name='quiz_items',
    )
    question = models.ForeignKey(
        'wagtailcore.Page',
        related_name='+',
    )
    weight = models.FloatField(
        _('value'),
        default=1.0,
        help_text=_(
            'The non-normalized weight of this item in the total quiz grade.'
        ),
    )

    # Wagtail admin
    panels = [
        panels.PageChooserPanel('question', [
            'cs_questioning.CodingIoQuestion',
            'cs_questioning.SimpleQuestion',
        ]),
        panels.FieldPanel('weight'),
    ]

    # # Migrations
    # base = models.OneToOneField(
    #     'cs_questions.QuizActivityItem',
    #     on_delete=models.SET_NULL,
    #     related_name='converted',
    #     blank=True,
    #     null=True,
    # )
    #
    # migrate_skip_attributes = Question.migrate_skip_attributes.union(
    #     {'long_description', 'value', 'comment', 'tolerance',
    #      'answer', 'question_ptr', 'grading_method', 'published_at',
    #      'quiz_grading_method', 'status', 'target_content_type', 'parent',
    #      'activity_ptr', 'target_id', 'owner_content_type', 'owner_id', 'index'}
    # )
    #
    # def migrate_question_T(x):
    #     try:
    #         return x.codingioquestion.converted
    #     except AttributeError:
    #         return x.numericquestion.converted
    #
    # def migrate_quiz_T(x):
    #     return x.converted
    #
    # @classmethod
    # def _migrate_post_conversions(cls, new):
    #     import json
    #     base = new.base
    #     new.body = json.dumps([{'value': base.long_description,
    #                             'type': 'markdown'}])
    #     new.save()
    #
    # def migrate_course_T(x):
    #     return x.converted


class Quiz(Activity):
    """
    Represent a quiz.
    """

    class Meta:
        verbose_name = _('quiz activity')
        verbose_name_plural = _('quiz activities')

    body = models.StreamField(
        QUESTION_STEM_BLOCKS,
        blank=True,
        null=True,
        verbose_name=_('Quiz description'),
        help_text=_(
            'This field should contain a text with any instructions, tips, or '
            'information that is relevant to the current quiz. Rembember to '
            'explain clearly the rules and what is expected from each student.'
        ),
    )
    language = models.ForeignKey(
        ProgrammingLanguage,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='quizzes',
        verbose_name=_('Programming language'),
        help_text=_(
            'Forces an specific programming language for all '
            'programing-related questions. If not given, will accept responses '
            'in any programming language.'
        ),
    )

    # Derived attributes
    questions = property(lambda x: list(x))
    num_questions = property(lambda x: x.quiz_items.count())

    def add_question(self, question):
        """
        Add a question to the quiz.
        """

        item = QuizItem(quiz=self, question=question)
        item.save()
        self.items.append(item)

    def get_user_response(self, user):
        """
        Return a response object for the given user.

        For now, users can only have one response.
        """

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

    def select_responses(self):
        return super().select_responses().filter(parent__isnull=True)

    # Wagtail admin
    parent_page_types = ['cs_core.Faculty']
    content_panels = Activity.content_panels + [
        panels.StreamFieldPanel('body'),
        panels.InlinePanel('quiz_items', label=_('Questions')),
    ]
    settings_panels = Activity.settings_panels + [
        panels.FieldPanel('language'),
    ]

    # # Migrations
    # base = models.OneToOneField(
    #     'cs_questions.QuizActivity',
    #     on_delete=models.SET_NULL,
    #     related_name='converted',
    #     blank=True,
    #     null=True,
    # )
    #
    # migrate_skip_attributes = Question.migrate_skip_attributes.union(
    #     {'long_description', 'value', 'comment', 'tolerance',
    #      'answer', 'question_ptr', 'grading_method', 'published_at',
    #      'quiz_grading_method', 'status', 'target_content_type', 'parent',
    #      'activity_ptr', 'target_id', 'owner_content_type', 'owner_id'}
    # )
    # migrate_attribute_conversions = dict(
    #     Question.migrate_attribute_conversions,
    #     long_description='body',
    #     discipline='course',
    # )
    #
    # def migrate_course_T(x):
    #     return x.courses.first().converted
    #
    # @classmethod
    # def migrate_post_conversions(cls, new):
    #     import json
    #     base = new.base
    #     new.body = json.dumps([{'value': base.long_description,
    #                             'type': 'markdown'}])
    #     new.save()
    #
    # def migrate_course_T(x):
    #     return x.converted


class QuizResponse(models.MigrateMixin, Response):
    """
    A response to a quiz activity.

    This object coordinate all responses for the questions registered in the
    quiz.
    """

    class Meta:
        proxy = True

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
            bool(CodingIoResponse.objects.filter(
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
            responses = set(CodingIoResponse.objects.filter(
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

    # # Migrations
    # migrate_skip_attributes = {'is_converted', 'response_ptr', 'id'}
    # migrate_attribute_conversions = {'question_for_unbound': 'question'}
    #
    # def migrate_question_T(x):
    #     return x.codingioquestion.converted
    #
    # def migrate_parent_T(x):
    #     if x is None:
    #         return None
    #     return x.converted
    #
    # def migrate_activity_T(x):
    #     return x.quizactivity.converted
    #
    # def migrate_feedback_data_T(x):
    #     return x or {}
    #
    # @classmethod
    # def migrate_qs(cls):
    #     from cs_questions.models import QuizResponse
    #     return QuizResponse.objects.all()
    #
    # @classmethod
    # def migrate_post_conversions(cls, new):
    #     base = new.base.quizresponse
    #     #new.save()
    #
    #     base.is_converted = True
    #     base.save()