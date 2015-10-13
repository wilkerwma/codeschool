from django.db import models
from codeschool.graders import PyIOGraderTemplate
from codeschool.parsers.io_question_template import parse_io_template


class QuestionBase(models.Model):

    '''Base class for all question types'''

    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=400, default='')
    description = models.TextField(default='')
    pub_date = models.DateTimeField('date published', auto_now_add=True)

    def __str__(self):
        return self.title


class QuestionIO(QuestionBase):

    '''QuestionIO objects represent a problem specified in the form of a set
    of desired input/output sequences in a program.'''

    # Additional fields
    correct_answer = models.TextField()
    examples = models.TextField()

    def _parse_examples(self):
        '''Return a parsed list of examples from the string of example
        descriptions'''

        return parse_io_template(self.examples)

    def _get_grader(self):
        '''Return a grader object for the given question'''

        parsed = self._parse_examples()
        return PyIOGraderTemplate(examples=parsed,
                                  answer=self.correct_answer,
                                  preprocessor='pytuga')

    def grade(self, response, timeout=0.5):
        '''Return a tuple of (grade, messages) with the numerical grade and
        a string with the formatted messages for the given grading job.'''

        grader = self._get_grader()
        return grader(response, timeout=timeout)


class Student(models.Model):
    name = models.CharField(max_length=200)
    school_id = models.CharField(max_length=20)

    def __str__(self):
        return '%s (%s)' % (self.school_id, self.name)

    def __repr__(self):
        return 'Student(%r, %r)' % (self.name, self.school_id)

    class Meta:
        unique_together = ('name', 'school_id')


class Answer(models.Model):
    student1 = models.ForeignKey(Student, related_name='answer_first')
    student2 = models.ForeignKey(
        Student,
        related_name='answer_second',
        null=True,
        blank=True)
    value = models.DecimalField(max_digits=5, decimal_places=2)
    question = models.ForeignKey(QuestionIO)
    response = models.TextField()
    timestamp = models.DateTimeField('time submmited', auto_now_add=True)

    def __repr__(self):
        grade = self.value
        id1 = self.student1.school_id
        id2 = getattr(self.student2, 'school_id', '*empty*')
        return 'Answer(grade=%s, id1=%s, id2=%s)' % (grade, id1, id2)


class Grade(models.Model):
    student = models.ForeignKey(Student)
    value = models.FloatField()
    feedback = models.TextField()
    answer = models.ForeignKey(Answer)
    timestamp = models.DateTimeField('time submmited')
