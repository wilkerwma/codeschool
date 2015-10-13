import functools
from decimal import Decimal
from codeschool.parsers import parse_io_template, In, Out, Prompt
from codeschool.graders import errors
from codeschool.graders.base import PythonTemplate
from codeschool.graders.util import print_str, message_bad_format, message_from_exception


class PyIOGraderTemplate(PythonTemplate):

    '''
    A template that specifies the expected sequence of input/output entries.

    The code is run and the final grade is computed from the ratio of correct
    outputs.
    '''

    def __init__(self, examples, *,
                 strict_caps=True, fuzzy_matching=True, **kwds):
        super().__init__(**kwds)

        if isinstance(examples, str):
            examples = parse_io_template(examples)
        self.examples = list(examples)
        self.fuzzy_matching = fuzzy_matching
        self.strict_caps = strict_caps

        if self.answer.strip():
            self.answer_code = self.validate(self.answer)
            self.examples = [self.check_answer(ex) for ex in self.examples]

    def check_answer(self, example):
        if all(isinstance(atom, In) for atom in example):
            inputs = [str(x) for x in example]
            return self.interact(self.answer_code, inputs)
        else:
            grade, msgs = self.grade_example(self.answer_code, example)
            if grade != 100:
                raise ValueError('bad_example', msgs)
        return example

    def namespace(self):
        '''Return a new namespace for execution'''

        import tugalib
        return vars(tugalib)

    def grade(self, code):
        try:
            code_obj = self.validate(code)
        except SyntaxError:
            ex = errors.BadSyntaxError()
            return Decimal(0), message_from_exception(ex)

        out = Decimal(100)

        for example in self.examples:
            grade, messages = self.grade_example(code_obj, example)
            if messages is None:
                out = min(grade, grade)
            else:
                return grade, messages
        return out, messages

    def interact(self, code_obj, inputs):
        namespace = self.namespace()
        inputs = list(reversed(inputs))
        interaction = []

        @functools.wraps(print)
        def print_func(*args, **kwds):
            data = print_str(*args, **kwds)
            if interaction and isinstance(interaction[-1], Out):
                data = interaction.pop() + data
            interaction.append(Out(data))

        @functools.wraps(input)
        def input_func(msg=None):
            if msg:
                interaction.append(Prompt(msg))
            try:
                data = inputs.pop()
            except IndexError:
                raise errors.DidNotTerminateError
            interaction.append(In(data))
            return data

        backup_print_input = print, input
        __builtins__['print'] = print_func
        __builtins__['input'] = input_func

        # Run code
        try:
            exec(code_obj, namespace)
        finally:
            __builtins__['print'], __builtins__['input'] = backup_print_input
        return interaction

    def grade_example(self, code_obj, example):
        inputs = [str(x) for x in example if x.is_input]

        try:
            interaction = self.interact(code_obj, inputs)
        except Exception as ex:
            return Decimal(0), message_from_exception(ex)
        else:
            if self.is_equivalent(interaction, example):
                return Decimal(100), None
            else:
                return Decimal(0), message_bad_format(interaction, example)

    def is_equivalent(self, interaction, example):
        '''Return True if the two interactions are equivalent.

        Normally it is used to compare the result of running a program with
        the expected example template.
        '''

        if len(interaction) != len(example):
            return False
        else:
            if interaction[:-1] != example[:-1]:
                return False
            elif interaction[-1].strip() != example[-1].strip():
                return False
            return True


if __name__ == '__main__':
    examples = parse_io_template('-->"hello world"')
    answer = 'print(print)'

    g = PyIOGraderTemplate(examples, answer=answer)
    print(g.grade("msg = 'hello world'\nprint(msg)"))
    print(g.grade("print('hi world')"))

    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    answer = '''
def soma(x, y):
    return x + y
'''
    tests = '''
assert 'soma' in globals(), 'Não apague ou renomeie a função soma()'
assert_equal(soma(1, 2), 3)
assert_similar(soma(1.0, 2.0), 3.0)
for x in [0, 1.0, 2, -1, -10]:
    for y in [0, 1.0, 2, -1, -10]:
        assert_similar(ANSWER.soma(x, y), soma(x, y))
'''
