The ``.markio`` format is a markdown-based format for representing IO based
programming questions. This library consists in a parser and a processor for
this format. It does not judge submissions by executing programming tasks and
comparing inputs/outputs but it provides some data structures that makes the
implementation of such a program much easier.


The syntax
==========

Markio files are regular markdown files with a conventional structure used to
represent an IO based programming question. The `markio`` parser processes the
markdown source and returns a dictionary with the document structure.
A ``.markio`` markdown file begins like this::

    Hello Person
    ============

        Author: Chips Chipperfield <chips@chipperfield.com>
        Slug: hello-person
        Timeout: 1s
        Tags: #begginer #basic

    A program that prints a personalized greeting to the user.

The document must start with an h1-level title corresponding to the question
title name. The title may be followed by an optional block with meta data.
Each metadata field is optional and only the fields shown above are supported.
The title and metadata information are accessible from the parsed structure
directly in the 'title', 'author', 'slug', etc keys.

Bellow that, it is possible to specify a single-paragraph short description.
This description is available both in the 'short_description' attribute of the
parsed structure.

The file than consists of various h2-sections. Most of these sections are
accessed in the parsed dictionary as a lowercase version of their title names::

    Description
    -----------

    Create a program that asks the user name and prints the message
    "Hello, <name>!" on the screen. The program output should be **exactelly**
    as requested, i.e., you should use **exactely** the same case and pontuaction
    marks as in the example string. You can assume that the input name is at
    most 100 characters long.

    ### Inputs

    A more thorough description of inputs.

    ### Outputs

    Description of the desired outputs.

This obligatory section contains a long description text for the question. It
accepts more or less arbitrary markdown text but all headings must be level 3
or above. The raw markdown can be accessed by the 'description' key in the
parsed structure.

::

    Example
    -------

        What is your name? <John>
        Hello John!

The 'example' section must contain a single block of ``.iospec`` data. For more
info check http://gihub.com/fabiommendes/iospec. IoSpec is a simple language
for specifying a sequence of inputs and outputs in a program interaction. Users
should avoid using input-only specifications in this section.

Although these examples might be used to judge submissions, the content of this
section is displayed to the student. Tests designed to judge a program should
go in the "Tests" section.


::

    Tests
    -----

        @input Mary
        @input mary
        @input Long Name
        @input $string[<100]

This section also contains a single block of ``.iospec`` data with the
various tests used to judge submissions. Input-only interactions are allowed
and encouraged.

::

    Placeholder
    -----------

        A paragraph with the defaut comments that should be included in the
        placeholder source.

This optional section is used to store the default comment string that should
be placed as the placeholder text in the ``<textarea>`` used in submission forms.

::

    Answer Key (Python3)
    -------------------

        # Indentation is necessary to mark source as a code block in markdown!

        name = input('What is your name? ')
        print('Hello, %s!' % name)

    Answer Key (C)
    --------------

        #include<stdio.h>

        main() {
            char buffer[101];

            puts("What is your name? ");
            scanf("%s", buffer);
            printf("Hello, %s!\n", buffer);
        }

This section defines a reference program that can be used to compute the correct
input/output sequences from the tests iospec. The reference solution can be
given in more than one language (which is specified inside parenthesis).
Markio do not grade or run these programs directly, however other graders may
use the redundant information to cross-check responses.

The source code can be accessed at ``parsed.answer_key['python3']``.

::

    Placeholder (Python3)
    ---------------------

        # Type here your response. Remember to use the print() and input()
        # functions

Finally, it is possible to define a per-language placeholder text. This overrides
the default placeholder input for a single specific language.

The placeholder code can be accessed at ``parsed.placehoder['python3']``.

::

    TLE Answer (python3)
    --------------------

    import time

    name = input('What is your name? ')
    time.sleep(1)
    print('Hello, %s!' % name)

The TLE (time limit exceeded) answer is used to calibrate the timeout for
submissions in a specific language. This section should contain the
implementation of an inefficient algorithm that the judge wants to disallow.
This is a robust method to specify the timeout that is calibrated to the host
machine processing power and is based on a well defined criteria rather than an
arbitrarily chosen duration.


Translations (not ready)
========================

Many programming quizzes involve internationalization-agnostic interactions.
They can be easily translated to different human languages since only the user
facing strings need to be adapted. If the input/output strings themselves need to
be translated, it is necessary to create a whole new markio file.

The translated sections can be put inside the main markio file or put on a
separate file. In the first case, it is necessary to append the language code
inside parenthesis after the section number (ex.: ``Description (pt-BR)``).
The placeholder text should be ``Placeholder (python3, pt-BR)``. The title,
short description and slug should be placed as metadata::

    Title (pt-BR): Olá Pessoa
    Slug (pt-BR): ola-pessoa
    Short description (pt-BR): Um programa que imprime uma saudação personalizada.

The alternative translation file should be named as ``<name>.pt_BR.markio``.
The markio parser accepts translated section names for many languages. The user
may choose to use the translated values or their english counterparts.

The default language is english. If the user does not need an english version
of the question, the main markio io file will be the same as a translation file.
In that case the filename is expected to be something like
``my-file.pt_BR.markio`` and all sections should be present. The markio parser
understands translated section names for a few languages. If your language is
not present, please contribute with translations!


Acessory files (not ready)
==========================

The content of all sections of a markio source that contains only a block of
source code (basically all sections but the title and description) can rather
be put inside a separate file. If the markio parser finds a file named
as ``my-file.answer_key.c`` in the same directory as the main source, it will
automatically fill the contents of the ``Answer Key (C)``. If both an external
source and the section content are present, the external file takes precedence.


Command line (not ready)
========================

This package installs the markio command that can perform several operations
on markio files.

...