from django.utils.translation import ugettext_lazy as _
from codeschool import models
from codeschool import blocks
from codeschool import panels
from cs_questions.models import Question, QuestionResponseItem
import cs_questions.blocks


class FormQuestion(Question):
    body = models.StreamField([
            ('numeric', blocks.NumericAnswerBlock()),
            ('boolean', blocks.BooleanAnswerBlock()),
            ('string', blocks.StringAnswerBlock()),
            ('date', blocks.DateAnswerBlock()),
            ('content', blocks.StreamBlock([
                ('description', blocks.RichTextBlock()),
                ('code', blocks.CodeBlock()),
                ('markdown', blocks.MarkdownBlock()),
                ('image', blocks.ImageChooserBlock()),
                ('document', blocks.DocumentChooserBlock()),
                ('page', blocks.PageChooserBlock()),
            ])),
        ],
        verbose_name=_('Fields'),
        help_text=_(
            'You can insert different types of fields for the student answers. '
            'This works as a simple form that accepts any combination of the'
            'different types of answer fields.'
        )
    )

    # Wagtail admin
    parent_page_types = ['cs_core.Faculty']
    content_panels = Question.content_panels[:]
    content_panels.insert(-1, panels.StreamFieldPanel('body'))

    # # Migration
    # base = models.OneToOneField(
    #     'cs_questions.NumericQuestion',
    #     on_delete=models.SET_NULL,
    #     related_name='converted',
    #     blank=True,
    #     null=True,
    # )
    #
    # migrate_skip_attributes = Question.migrate_skip_attributes.union(
    #     {'long_description', 'value', 'comment', 'tolerance',
    #      'answer', 'question_ptr'}
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
    #     new.body = json.dumps([{'value': {
    #                 'name': 'Resposta',
    #                 'tolerance': str(base.tolerance),
    #                 'answer': str(base.answer),
    #                 'value': 1.0,
    #             }, 'type': 'numeric'}])
    #     new.stem = json.dumps([{'value': base.long_description, 'type': 'markdown'}])
    #     new.save()


class FormResponseItem(models.MigrateMixin, QuestionResponseItem):
    class Meta:
        proxy = True

    # # Migrations
    # migrate_skip_attributes = {'is_converted', 'value', 'response_ptr', 'id'}
    # migrate_attribute_conversions = {'question_for_unbound': 'question'}
    #
    # def migrate_question_T(x):
    #     return x.numericquestion.converted
    #
    # def migrate_parent_T(x):
    #     if x is None:
    #         return None
    #     return x.converted
    #
    # @classmethod
    # def migrate_qs(cls):
    #     from cs_questions.models import NumericResponse
    #     return NumericResponse.objects.all()
    #
    # def migrate_post_conversions(new):
    #     base = new.base.numericresponse
    #     question = base.question_for_unbound or base.activity.numericquestionactivity.question
    #     new.response_data = [{'type': 'numeric', 'response': base.value, 'block': 0}]
    #     new.activity = question.numericquestion.converted
    #     new.feedback_data = {}
    #     new.save()
    #
    #     base.is_converted = True
    #     base.save()
