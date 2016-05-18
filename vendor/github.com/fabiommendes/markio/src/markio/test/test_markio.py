import os
import io
import pytest
import markio


DIRNAME = os.path.dirname(__file__)


@pytest.fixture
def hello():
    path = os.path.join(DIRNAME, 'hello-person.md')
    return markio.parse(path)


@pytest.fixture
def markio_example_1():
    path = os.path.join(DIRNAME, 'markio-example-1.md')
    return open(path).read()


def test_pprint(hello):
    F = io.StringIO()
    hello.pprint(file=F)
    st = r"""
{'answer_key': {'c': '#include<stdio.h>\n'
                     '\n'
                     'main() {\n'
                     '    char buffer[101];\n'
                     '\n'
                     '    puts("What is your name? ");\n'
                     '    scanf("%s", buffer);\n'
                     '    printf("Hello, %s!\\n", buffer);\n'
                     '}',
                'python3': '# This indentation is necessary to mark source as '
                           'a code block in\n'
                           '# markdown!\n'
                           '\n'
                           "name = input('What is your name? ')\n"
                           "print('Hello, %s!' % name)"},
 'author': 'Chips Chipperfield <chips@chipperfield.com>',
 'description': 'Create a program that asks the user name and prints the '
                'message\n'
                '"Hello, <name>!" on the screen. The program output should be '
                '**exactly**\n'
                'as requested, i.e., you should use **exactly** the same case '
                'and punctuation\n'
                'marks as in the example string. You can assume that the input '
                'name is at\n'
                'most 100 characters long.',
 'example': 'What is your name? <John>\nHello John!',
 'placeholder': {None: 'Type here your response.',
                 'python3': '# Type here your response. Remember to use the '
                            'print() and input()\n'
                            '# functions'},
 'short_description': 'A program that prints a personalized greeting to the '
                      'user.',
 'slug': 'hello-person',
 'tags': ['begginer', 'basic'],
 'tests': '@input\n'
          '    Mary\n'
          '\n'
          '@input\n'
          '    mary\n'
          '\n'
          '@input\n'
          '    Long Name\n'
          '\n'
          '@input\n'
          '    $string[<100]',
 'timeout': 1.0,
 'title': 'Hello Person'}"""
    assert F.getvalue().strip() == st.strip()


def test_round_trip(hello):
    path = os.path.join(DIRNAME, 'hello-person.md')
    with open(path) as F:
        assert hello.source() == F.read()


def test_hello_parsing(hello):
    assert hello.title == 'Hello Person'
    assert None not in hello.answer_key


def test_markio_example_1_parsing(markio_example_1):
    obj = markio.parse_string(markio_example_1)
    assert obj.pformat().strip() == r'''
{'author': 'Chips',
 'description': 'Long description\n\n### Sub-session\n\nSomething else...',
 'short_description': 'Short description.',
 'title': 'Example1'}'''.strip()


def test_stripped_code(hello):
    for code in hello.answer_key.values():
        assert not code.endswith('\n\n')


def test_source_renderer():
    tree = markio.Markio(
        title='foo',
        author='bar',
        timeout=1,
        description='description',
    )

    assert '===' in tree.source()


if __name__ == '__main__':
    pytest.main('test_markio.py')