Hello Person
============

    Author: Chips Chipperfield <chips@chipperfield.com>
    Slug: hello-person
    Timeout: 1.0
    Tags: #begginer #basic

A program that prints a personalized greeting to the user.


Description
-----------

Create a program that asks the user name and prints the message
"Hello, <name>!" on the screen. The program output should be **exactly**
as requested, i.e., you should use **exactly** the same case and punctuation
marks as in the example string. You can assume that the input name is at
most 100 characters long.

Example
-------

    What is your name? <John>
    Hello John!

Tests
-----

    @input
        Mary

    @input
        mary

    @input
        Long Name

    @input
        $string[<100]


Answer Key (c)
--------------

    #include<stdio.h>

    main() {
        char buffer[101];

        puts("What is your name? ");
        scanf("%s", buffer);
        printf("Hello, %s!\n", buffer);
    }

Answer Key (python3)
--------------------

    # This indentation is necessary to mark source as a code block in
    # markdown!

    name = input('What is your name? ')
    print('Hello, %s!' % name)


Placeholder
-----------

    Type here your response.

Placeholder (python3)
---------------------

    # Type here your response. Remember to use the print() and input()
    # functions