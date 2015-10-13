from decimal import Decimal
from codeschool.graders import errors
from codeschool.graders.util import timeout, message_from_exception


class GraderTemplate(object):

    '''
    :cls:`GraderTemplate` objects are use to grade code submited to some
    specific coding problem.
    '''

    def __init__(self, *, answer=None, max_runtime=None):
        self.answer = answer
        self.max_runtime = max_runtime

    def validate(self, code):
        '''Raise a `BadSyntaxError` if the string of code has some syntax
        error.
        '''

        raise NotImplementedError

    def grade(self, code):
        '''Run grading and return a :cls:`Grade` object with the grade
        associated to code.'''

        raise NotImplementedError

    def timed_grading(self, code, time=1):
        '''Run grading job with a timeout'''

        try:
            return timeout(self.grade, args=(code,), timeout=time)
        except TimeoutError:
            ex = errors.TimeExceededError()
            return Decimal(0), message_from_exception(ex)

    def __call__(self, code, timeout=None):
        if timeout is not None:
            return self.timed_grading(code, timeout)
        else:
            return self.grade(code)


class PythonTemplate(GraderTemplate):

    '''
    A validator that assumes a Python code input.

    Users can specify a pre-processor that changes the input code prior
    processing. The preprocessor can insert imports, block some language
    features or perform arbitrary code transformations.
    '''
    _preprocessors = {}

    def __init__(self, *, preprocessor=lambda x: x, **kwds):
        D = self._preprocessors
        self.preprocessor = D.get(preprocessor, preprocessor)
        super().__init__(**kwds)

    def validate(self, code):
        code = self.preprocessor(code)
        return compile(code, '<input>', 'exec')

    def execute(self, code):
        '''Execute some Python code and return the resulting namespace.'''

        code_obj = self.validate(code)
        namespace = {}
        exec(code_obj, namespace)
        return namespace

    @classmethod
    def register_preprocessor(cls, name, value=None):
        '''Register a pre-processor function.

        A registered preprocessor can be referenced by name in the
        instantiation of a PythonTemplate object.

        Example
        -------

        >>> from pytuga import transpile
        >>> PythonTemplate.register_preprocessor('pytuga', transpile)
        '''
        # Decorator form
        if value is None:
            def decorator(func):
                cls.register_preprocessor(name, func)
                return func
            return decorator

        cls._preprocessors[name] = value
