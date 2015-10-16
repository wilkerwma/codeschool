import copy
import judge
from picklefield import PickledObjectField
from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string

class Data(object):
    pass

class BaseModel(models.Model):
    class Meta:
        abstract = True
    
    def card(self):
        '''Represents a card with objects information'''
        
        name = type(self).__name__.lower()
        return render_to_string('cs_app/cards/%s.html' % name, 
                                context={name: self})



class Discipline(models.Model):
    '''Organizes questions, teachers and students into disciplines'''
    
    name = models.CharField(max_length=200)
    teacher = models.ForeignKey(User, related_name='owned_disciplines')
    students = models.ManyToManyField(User, related_name='disciplines')
    passphrase = models.CharField(max_length=100)
    timestamp = models.DateTimeField('time created', auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    

class Quiz(models.Model):
    '''Organizes list_questions, teachers and students into disciplines'''
    
    name = models.CharField(max_length=200)
    questions = models.ManyToManyField('Question')
    discipline = models.ForeignKey(Discipline)
    start_time = models.DateTimeField(auto_now_add=True)
    start_end = models.DateTimeField(null=True)
    timestamp = models.DateTimeField('time submmited', auto_now_add=True)
        
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'quizzes'


class Question(BaseModel):
    '''Represents a question object'''
    
    # Enumerations for question types
    IO, FUNCTION = range(2)
    
    # Fields
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=400, default='')
    description = models.TextField(default='')
    visible = models.BooleanField(default=False)
    question_type = models.PositiveSmallIntegerField(default=IO)
    grading = models.TextField(default='')
    document = PickledObjectField(null=True)
    prepared = PickledObjectField(null=True)
    timestamp = models.DateTimeField('time submmited', auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        permissions = (("download_question", "Can download question files"),)
        
    #
    # API methods
    #
    def __check_question_type(self):
        if self.question_type != 0:
            raise ValueError('invalid question type: %s' % self.question_type)
        
    @property
    def __document(self):
        '''Safe version of document: create a new document when attribute is 
        empty'''
        
        if self.document is None:
            self.__check_question_type()
            if self.question_type == self.IO:
                document = judge.parsers.QuestionIODocument()
                document.title = self.title
                document.subtitle = self.short_description
                document.description = self.description
                document.answer = self.answer
                document.examples = self.grading
                self.document = document
        return self.document
    
    @property
    def __prepared(self):
        '''Safe version of prepared'''
        
        if self.prepared is None:
            self.prepare()
        return self.prepared
    
    def __get_lang_dict(self, queryset):
        D = {}
        for ans in queryset:
            D[ans.language] = ans.text
        return D
    
    def answer(self, lang='all'):
        '''Return the registered answer for the given language.
        
        If lang='all', return a mapping from all languages to their respective
        placeholder text.
        '''
        
        if lang == 'all':
            return self.__get_lang_dict(self.answers.all())
        else:
            try:
                return self.answers.get(language=lang).data
            except QuestionAnswer.DoesNotExist:
                return None
    
    def placeholder(self, lang='all'):
        '''Return the registered placeholder text for the given language.
        
        If lang='all', return a mapping from all languages to their respective
        placeholder text.'''
        
        if lang == 'all':
            return self.__get_lang_dict(self.placeholders.all())
        else:
            try:
                return self.placeholders.get(language=lang).data
            except QuestionPlaceholder.DoesNotExist:
                return None
        
    def grade_response(self, response, timeout=1.0):
        '''Return a Response object with the the numerical grade and feedback
        messages for the given response.
        
        The response is created, but is not automatically saved to the 
        database.'''

        self.__check_question_type()
        if self.question_type == self.IO:
            template = self.__prepared.template
            grade, feedback = judge.graders.grade_code(
                response, 
                template, 
                timeout=timeout,
                feedback='html',
                sandbox=True)
            grade *= 100
        
        return Response(question=self, 
                        grade=grade, 
                        feedback=feedback, 
                        text=response)
        
    def prepare(self):
        '''Execute before insertion into the database'''
    
        fields = self.prepared = Data()
        fields.errors = None
            
        self.__check_question_type()
        if self.question_type == self.IO:
            examples = self.__document.examples
            answer = self.__document.answer('python')
            fields.template = judge.graders.run_code(answer, examples)
            
    def full_document(self):
        '''Safe version of document: create a new document when attribute is 
        empty'''
        
        document = copy.deepcopy(self.__document) 
        document.title = self.title
        document.subtitle = self.short_description
        document.description = self.description
        document.answers = self.answer('all')
        document.placeholders = self.placeholder('all')
        return document

    def document_text(self):
        '''Return a text representation of itself'''
        return self.full_document().source()
    
    
class QuestionAnswer(BaseModel):
    '''Represents an answer to some question given in some specific computer
    language'''
    
    language = models.CharField(max_length=20, default='python')
    question = models.ForeignKey(Question, related_name='answers')
    data = models.TextField()
    
    class Meta:
        unique_together = (('language', 'question'),) 

class QuestionPlaceholder(BaseModel):
    '''Represents a placeholder text to some question given in some specific 
    computer language'''
    
    language = models.CharField(max_length=20, default='python')
    question = models.ForeignKey(Question, related_name='placeholders')
    data = models.TextField()
    
    class Meta:
        unique_together = (('language', 'question'),)
    
class Response(models.Model):
    '''
    Represents a student's response to some question. The student may submmit
    many responses for the same object. It is also possible to submmit 
    different responses with different students. 
    '''
    
    question = models.ForeignKey(Question)
    student = models.ForeignKey(User, null=True)
    related = models.ManyToManyField('Response', blank=True)
    text = models.TextField()
    feedback = models.TextField(default='', blank=True, null=True)
    grade = models.DecimalField(
        'a percentage of maximum grade', 
        max_digits=6, 
        decimal_places=2,
        default=0,
    )
    
    timestamp = models.DateTimeField(
        'time submmited', 
        auto_now_add=True
    )

    def __repr__(self):
        grade = getattr(self, 'grade', None)
        question = getattr(self, 'question', None)
        return 'Response(grade=%s, question=%s)' % (grade, question) 

    @property
    def has_errors(self):
        return self.grade != 100
        
    class Meta:
        permissions = (("see_all_responses", "Can see all responses"),)
        
    def save_as_team(self, students):
        '''Saves a copy of a response object for each of the given students in
        the input list. It assumes as if all students in the group collaborated
        to produce the given response'''
        
        students = list(students)
        N = len(students)
        if len(set(students)) != N:
            raise ValueError('students must be unique')
        
        # Create copies
        kwds = dict(
            question=self.question, 
            text=self.text, 
            feedback=self.feedback, 
            grade=self.grade, 
            timestamp=self.timestamp)
        copies = [self]
        copies.extend(Response(**kwds) for _ in range(N - 1))
        
        
        # Save each copy before setting the many-to-many relations
        for copy, student in zip(copies, students):
            copy.student = student
            copy.save()
        
        # Create all relations
        for i in range(N):
            for j in range(i + 1, N):        
                copies[i].related.add(copies[j])

        # Save again with new parameters
        for copy in copies:
            copy.save()