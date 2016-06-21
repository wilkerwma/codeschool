from decimal import Decimal
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from codeschool import models
from codeschool import panels
from cs_core.models import ProgrammingLanguage, Activity, Response, ResponseItem
from cs_questions.models import Question, QUESTION_STEM_BLOCKS


class QuizItem(models.Orderable):
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
            'cs_questions.CodingIoQuestion',
            'cs_questions.FormQuestion',
        ]),
        panels.FieldPanel('weight'),
    ]


class Quiz(Activity):
    """
    A quiz that may contain several different questions.
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
            'information that is relevant to the current quiz. Remember to '
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
            'Forces an specific programming language for all programing '
            'related questions. If not given, will accept responses in any '
            'programming language. This has no effect in non-programming '
            'activities.'
        ),
    )

    # Derived attributes
    questions = property(lambda x: [i.question for i in x.quiz_items.all()])
    num_questions = property(lambda x: x.quiz_items.count())

    def add_question(self, question, weight=1.0):
        """
        Add a question to the quiz.
        """

        self.quiz_items.create(question=question, weight=weight)
        item = QuizItem(quiz=self, question=question)
        item.save()
        self.items.append(item)

    def register_response_item(self, *, user=None, context=None, **kwargs):
        """
        Return a response object for the given user.

        For now, users can only have one response.
        """

        # Silently ignore autograde
        kwargs.pop('autograde', None)

        # Quiz responses do not accept any extra parameters in the constructor
        if kwargs:
            param = kwargs.popitem()[0]
            raise TypeError('invalid parameter: %r' % param)

        # We force that quiz responses have a single response_item which is
        # only updated by the process_response_item() method.
        response = self.get_response(user, context)
        if response.items.count() != 0:
            return response.items.first()

        return super().register_response_item(user=user, context=context)

    def process_response_item(self, response, recycled=False):
        """
        Process a question response and adds a reference to it in the related
        QuizResponseItem.
        """

        # We do not register recycled responses
        if not recycled:
            user = response.user
            context = response.context
            quiz_response_item = self.register_response_item(user=user,
                                                             context=context)
            quiz_response_item.register_response(response)

    # Wagtail admin
    parent_page_types = ['cs_questions.QuizList']
    content_panels = Activity.content_panels + [
        panels.StreamFieldPanel('body'),
        panels.InlinePanel('quiz_items', label=_('Questions')),
    ]
    settings_panels = Activity.settings_panels + [
        panels.FieldPanel('language'),
    ]


class QuizResponseItem(ResponseItem):
    """
    A response to a quiz activity.

    This object coordinate all responses for the questions registered in the
    quiz.
    """

    class Meta:
        proxy = True

    @property
    def quiz(self):
        return self.activity.specific

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.response_data:
            questions = self.quiz.questions
            data = {str(question.id): [] for question in questions}
            self.response_data = data

    def register_response(self, response, commit=True):
        """
        Register a question response to itself.
        """

        id = str(response.question_id)
        self.response_data[id].append(response.id)
        if commit:
            self.save(update_fields=['response_data'])

    def is_answered(self, question=None):
        """
        Return True if question has been answered in the quiz.

        If no question is given, return True if all questions were answered.
        """

        if question is None:
            return all(len(lst) > 0 for lst in self.response_data.values())
        else:
            return len(self.response_data[str(question.id)]) > 0

    def unanswered(self):
        """
        Return a list with all unanswered questions for this quiz.
        """

        question_ids = [id for (id, L) in self.response_data.items() if not L]
        return [p.specific for p in Page.objects.filter(id__in=question_ids)]

    def autograde_compute(self):
        grades = []

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

Quiz.response_item_class = QuizResponseItem