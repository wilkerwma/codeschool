# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-19 01:17
from __future__ import unicode_literals

import codeschool.blocks.ace
import codeschool.blocks.core
import codeschool.models.mixins
import codeschool.models.wagtail
import cs_core.models.activity.activity_base
import cs_core.models.activity.response_context
import cs_core.models.activity.grading_method
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.contrib.wagtailroutablepage.models
import wagtail.wagtailcore.blocks
import wagtail.wagtailcore.fields
import wagtail.wagtaildocs.blocks
import wagtail.wagtailembeds.blocks
import wagtail.wagtailimages.blocks
import wagtail.wagtailsnippets.blocks
import wagtailmarkdown.blocks


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0028_merge'),
        ('cs_core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnswerKeyItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.TextField(blank=True, help_text='Source code for the correct answer in the given programming language.', verbose_name='answer source code')),
                ('placeholder', models.TextField(blank=True, help_text='This optional field controls which code should be placed in the source code editor when a question is opened. This is useful to put boilerplate or even a full program that the student should modify. It is possible to configure a global per-language boilerplate and leave this field blank.', verbose_name='placeholder source code')),
                ('source_hash', models.CharField(help_text='Hash computed from the reference source', max_length=32)),
                ('iospec_hash', models.CharField(help_text='Hash computed from reference source and iospec_size.', max_length=32)),
                ('iospec_source', models.TextField(blank=True, help_text='Iospec source for the expanded testcase. This data is computed from the reference iospec source and the given reference program to expand the outputs from the given inputs.', verbose_name='expanded source')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer_keys', to='cs_core.ProgrammingLanguage')),
            ],
            options={
                'verbose_name_plural': 'answer keys',
                'verbose_name': 'answer key',
            },
            bases=(codeschool.models.mixins.MigrateMixin, models.Model),
        ),
        migrations.CreateModel(
            name='CodingIoQuestion',
            fields=[
                ('page_ptr', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='codingioquestion_instance', serialize=False, to='wagtailcore.Page')),
                ('content_color', models.CharField(default='#10A2A4', help_text='Personalize the main color for page content.', max_length=20, verbose_name='color')),
                ('short_description', models.CharField(blank=True, help_text='A very brief one-phrase description used in listings.', max_length=140, verbose_name='short description')),
                ('icon_src', models.CharField(blank=True, help_text='Optional icon name that can be used to personalize the activity. Material icons are available by using the "material:" namespace as in "material:menu".', max_length=50, verbose_name='activity icon')),
                ('resources', wagtail.wagtailcore.fields.StreamField((('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('embed', wagtail.wagtailembeds.blocks.EmbedBlock()), ('markdown', wagtailmarkdown.blocks.MarkdownBlock()), ('url', wagtail.wagtailcore.blocks.URLBlock()), ('text', wagtail.wagtailcore.blocks.TextBlock()), ('char', wagtail.wagtailcore.blocks.CharBlock()), ('ace', codeschool.blocks.ace.AceBlock()), ('bool', wagtail.wagtailcore.blocks.BooleanBlock()), ('doc', wagtail.wagtaildocs.blocks.DocumentChooserBlock()), ('snippet', wagtail.wagtailsnippets.blocks.SnippetChooserBlock(cs_core.models.activity.grading_method.GradingMethod)), ('date', wagtail.wagtailcore.blocks.DateBlock()), ('time', wagtail.wagtailcore.blocks.TimeBlock()), ('stream', wagtail.wagtailcore.blocks.StreamBlock((('page', wagtail.wagtailcore.blocks.PageChooserBlock()), ('html', wagtail.wagtailcore.blocks.RawHTMLBlock()))))))),
                ('stem', wagtail.wagtailcore.fields.StreamField((('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('heading', wagtail.wagtailcore.blocks.CharBlock(classname='full title')), ('code', wagtail.wagtailcore.blocks.StructBlock((('language', wagtail.wagtailcore.blocks.ChoiceBlock(choices=[('ace/mode/abap', 'ABAP'), ('ace/mode/abc', 'ABC'), ('ace/mode/actionscript', 'ActionScript'), ('ace/mode/ada', 'ADA'), ('ace/mode/apache_conf', 'Apache Conf'), ('ace/mode/asciidoc', 'AsciiDoc'), ('ace/mode/assembly_x86', 'Assembly x86'), ('ace/mode/autohotkey', 'AutoHotKey'), ('ace/mode/batchfile', 'BatchFile'), ('ace/mode/c_cpp', 'C and C++'), ('ace/mode/c9search', 'C9Search'), ('ace/mode/cirru', 'Cirru'), ('ace/mode/clojure', 'Clojure'), ('ace/mode/cobol', 'Cobol'), ('ace/mode/coffee', 'CoffeeScript'), ('ace/mode/coldfusion', 'ColdFusion'), ('ace/mode/csharp', 'C#'), ('ace/mode/css', 'CSS'), ('ace/mode/curly', 'Curly'), ('ace/mode/d', 'D'), ('ace/mode/dart', 'Dart'), ('ace/mode/diff', 'Diff'), ('ace/mode/django', 'Django'), ('ace/mode/dockerfile', 'Dockerfile'), ('ace/mode/dot', 'Dot'), ('ace/mode/dummy', 'Dummy'), ('ace/mode/dummysyntax', 'DummySyntax'), ('ace/mode/eiffel', 'Eiffel'), ('ace/mode/ejs', 'EJS'), ('ace/mode/elixir', 'Elixir'), ('ace/mode/elm', 'Elm'), ('ace/mode/erlang', 'Erlang'), ('ace/mode/forth', 'Forth'), ('ace/mode/ftl', 'FreeMarker'), ('ace/mode/gcode', 'Gcode'), ('ace/mode/gherkin', 'Gherkin'), ('ace/mode/gitignore', 'Gitignore'), ('ace/mode/glsl', 'Glsl'), ('ace/mode/gobstones', 'Gobstones'), ('ace/mode/golang', 'Go'), ('ace/mode/groovy', 'Groovy'), ('ace/mode/haml', 'HAML'), ('ace/mode/handlebars', 'Handlebars'), ('ace/mode/haskell', 'Haskell'), ('ace/mode/haxe', 'haXe'), ('ace/mode/html', 'HTML'), ('ace/mode/html_elixir', 'HTML (Elixir)'), ('ace/mode/html_ruby', 'HTML (Ruby)'), ('ace/mode/ini', 'INI'), ('ace/mode/io', 'Io'), ('ace/mode/jack', 'Jack'), ('ace/mode/jade', 'Jade'), ('ace/mode/java', 'Java'), ('ace/mode/javascript', 'JavaScript'), ('ace/mode/json', 'JSON'), ('ace/mode/jsoniq', 'JSONiq'), ('ace/mode/jsp', 'JSP'), ('ace/mode/jsx', 'JSX'), ('ace/mode/julia', 'Julia'), ('ace/mode/latex', 'LaTeX'), ('ace/mode/lean', 'Lean'), ('ace/mode/less', 'LESS'), ('ace/mode/liquid', 'Liquid'), ('ace/mode/lisp', 'Lisp'), ('ace/mode/livescript', 'LiveScript'), ('ace/mode/logiql', 'LogiQL'), ('ace/mode/lsl', 'LSL'), ('ace/mode/lua', 'Lua'), ('ace/mode/luapage', 'LuaPage'), ('ace/mode/lucene', 'Lucene'), ('ace/mode/makefile', 'Makefile'), ('ace/mode/markdown', 'Markdown'), ('ace/mode/mask', 'Mask'), ('ace/mode/matlab', 'MATLAB'), ('ace/mode/maze', 'Maze'), ('ace/mode/mel', 'MEL'), ('ace/mode/mushcode', 'MUSHCode'), ('ace/mode/mysql', 'MySQL'), ('ace/mode/nix', 'Nix'), ('ace/mode/nsis', 'NSIS'), ('ace/mode/objectivec', 'Objective-C'), ('ace/mode/ocaml', 'OCaml'), ('ace/mode/pascal', 'Pascal'), ('ace/mode/perl', 'Perl'), ('ace/mode/pgsql', 'pgSQL'), ('ace/mode/php', 'PHP'), ('ace/mode/powershell', 'Powershell'), ('ace/mode/praat', 'Praat'), ('ace/mode/prolog', 'Prolog'), ('ace/mode/properties', 'Properties'), ('ace/mode/protobuf', 'Protobuf'), ('ace/mode/python', 'Python'), ('ace/mode/r', 'R'), ('ace/mode/razor', 'Razor'), ('ace/mode/rdoc', 'RDoc'), ('ace/mode/rhtml', 'RHTML'), ('ace/mode/rst', 'RST'), ('ace/mode/ruby', 'Ruby'), ('ace/mode/rust', 'Rust'), ('ace/mode/sass', 'SASS'), ('ace/mode/scad', 'SCAD'), ('ace/mode/scala', 'Scala'), ('ace/mode/scheme', 'Scheme'), ('ace/mode/scss', 'SCSS'), ('ace/mode/sh', 'SH'), ('ace/mode/sjs', 'SJS'), ('ace/mode/smarty', 'Smarty'), ('ace/mode/snippets', 'snippets'), ('ace/mode/soy_template', 'Soy Template'), ('ace/mode/space', 'Space'), ('ace/mode/sql', 'SQL'), ('ace/mode/sqlserver', 'SQLServer'), ('ace/mode/stylus', 'Stylus'), ('ace/mode/svg', 'SVG'), ('ace/mode/swift', 'Swift'), ('ace/mode/tcl', 'Tcl'), ('ace/mode/tex', 'Tex'), ('ace/mode/text', 'Text'), ('ace/mode/textile', 'Textile'), ('ace/mode/toml', 'Toml'), ('ace/mode/twig', 'Twig'), ('ace/mode/typescript', 'Typescript'), ('ace/mode/vala', 'Vala'), ('ace/mode/vbscript', 'VBScript'), ('ace/mode/velocity', 'Velocity'), ('ace/mode/verilog', 'Verilog'), ('ace/mode/vhdl', 'VHDL'), ('ace/mode/wollok', 'Wollok'), ('ace/mode/xml', 'XML'), ('ace/mode/xquery', 'XQuery'), ('ace/mode/yaml', 'YAML')])), ('source', codeschool.blocks.ace.AceBlock())))), ('markdown', wagtailmarkdown.blocks.MarkdownBlock())), blank=True, help_text='Describe what the question is asking and how should the students answer it as clearly as possible. Good questions should not be ambiguous.', null=True, verbose_name='Question description')),
                ('author_name', models.CharField(blank=True, help_text="The author's name, if not the same user as the question owner.", max_length=100, verbose_name="Author's name")),
                ('comments', wagtail.wagtailcore.fields.RichTextField(blank=True, help_text='(Optional) Any private information that you want to associate to the question page.', verbose_name='Comments')),
                ('iospec_size', models.PositiveIntegerField(default=10, help_text='The desired number of test cases that will be computed after comparing the iospec template with the answer key. This is only a suggested value and will only be applied if the response template uses input commands to generate random input.', verbose_name='number of iospec template expansions')),
                ('iospec_source', models.TextField(help_text='Template used to grade I/O responses. See http://pythonhosted.org/iospec for a complete reference on the template format.', verbose_name='response template')),
                ('iospec_hash', models.CharField(help_text='A hash to keep track of iospec updates.', max_length=32)),
                ('timeout', models.FloatField(blank=True, default=1.0, help_text='Defines the maximum runtime the grader will spend evaluating each test case.', verbose_name='timeout in seconds')),
                ('is_usable', models.BooleanField(help_text='Tells if the question has at least one usable iospec entry. A complete iospec may be given from a single iospec source or by a combination of a valid source and a reference computer program.', verbose_name='is usable')),
                ('is_consistent', models.BooleanField(help_text='Checks if all given answer keys are consistent with each other. The question might become inconsistent by the addition of an reference program that yields different results from the equivalent program in a different language.', verbose_name='is consistent')),
                ('grading_method', models.ForeignKey(blank=True, default=cs_core.models.activity.response_context.grading_method_best, help_text='Choose the strategy for grading this activity.', on_delete=django.db.models.deletion.SET_DEFAULT, to='cs_core.GradingMethod')),
            ],
            options={
                'verbose_name_plural': 'input/output questions',
                'verbose_name': 'input/output question',
            },
            bases=(wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin, codeschool.models.mixins.CopyMixin, codeschool.models.wagtail.CodeschoolPageMixin, codeschool.models.mixins.MigrateMixin, 'wagtailcore.page'),
        ),
        migrations.CreateModel(
            name='QuestionList',
            fields=[
                ('page_ptr', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='questionlist_instance', serialize=False, to='wagtailcore.Page')),
                ('content_color', models.CharField(default='#10A2A4', help_text='Personalize the main color for page content.', max_length=20, verbose_name='color')),
            ],
            options={
                'abstract': False,
            },
            bases=(codeschool.models.wagtail.CodeschoolPageMixin, codeschool.models.mixins.MigrateMixin, 'wagtailcore.page'),
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('page_ptr', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='quiz_instance', serialize=False, to='wagtailcore.Page')),
                ('content_color', models.CharField(default='#10A2A4', help_text='Personalize the main color for page content.', max_length=20, verbose_name='color')),
                ('short_description', models.CharField(blank=True, help_text='A very brief one-phrase description used in listings.', max_length=140, verbose_name='short description')),
                ('icon_src', models.CharField(blank=True, help_text='Optional icon name that can be used to personalize the activity. Material icons are available by using the "material:" namespace as in "material:menu".', max_length=50, verbose_name='activity icon')),
                ('resources', wagtail.wagtailcore.fields.StreamField((('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('embed', wagtail.wagtailembeds.blocks.EmbedBlock()), ('markdown', wagtailmarkdown.blocks.MarkdownBlock()), ('url', wagtail.wagtailcore.blocks.URLBlock()), ('text', wagtail.wagtailcore.blocks.TextBlock()), ('char', wagtail.wagtailcore.blocks.CharBlock()), ('ace', codeschool.blocks.ace.AceBlock()), ('bool', wagtail.wagtailcore.blocks.BooleanBlock()), ('doc', wagtail.wagtaildocs.blocks.DocumentChooserBlock()), ('snippet', wagtail.wagtailsnippets.blocks.SnippetChooserBlock(cs_core.models.activity.grading_method.GradingMethod)), ('date', wagtail.wagtailcore.blocks.DateBlock()), ('time', wagtail.wagtailcore.blocks.TimeBlock()), ('stream', wagtail.wagtailcore.blocks.StreamBlock((('page', wagtail.wagtailcore.blocks.PageChooserBlock()), ('html', wagtail.wagtailcore.blocks.RawHTMLBlock()))))))),
                ('body', wagtail.wagtailcore.fields.StreamField((('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('heading', wagtail.wagtailcore.blocks.CharBlock(classname='full title')), ('code', wagtail.wagtailcore.blocks.StructBlock((('language', wagtail.wagtailcore.blocks.ChoiceBlock(choices=[('ace/mode/abap', 'ABAP'), ('ace/mode/abc', 'ABC'), ('ace/mode/actionscript', 'ActionScript'), ('ace/mode/ada', 'ADA'), ('ace/mode/apache_conf', 'Apache Conf'), ('ace/mode/asciidoc', 'AsciiDoc'), ('ace/mode/assembly_x86', 'Assembly x86'), ('ace/mode/autohotkey', 'AutoHotKey'), ('ace/mode/batchfile', 'BatchFile'), ('ace/mode/c_cpp', 'C and C++'), ('ace/mode/c9search', 'C9Search'), ('ace/mode/cirru', 'Cirru'), ('ace/mode/clojure', 'Clojure'), ('ace/mode/cobol', 'Cobol'), ('ace/mode/coffee', 'CoffeeScript'), ('ace/mode/coldfusion', 'ColdFusion'), ('ace/mode/csharp', 'C#'), ('ace/mode/css', 'CSS'), ('ace/mode/curly', 'Curly'), ('ace/mode/d', 'D'), ('ace/mode/dart', 'Dart'), ('ace/mode/diff', 'Diff'), ('ace/mode/django', 'Django'), ('ace/mode/dockerfile', 'Dockerfile'), ('ace/mode/dot', 'Dot'), ('ace/mode/dummy', 'Dummy'), ('ace/mode/dummysyntax', 'DummySyntax'), ('ace/mode/eiffel', 'Eiffel'), ('ace/mode/ejs', 'EJS'), ('ace/mode/elixir', 'Elixir'), ('ace/mode/elm', 'Elm'), ('ace/mode/erlang', 'Erlang'), ('ace/mode/forth', 'Forth'), ('ace/mode/ftl', 'FreeMarker'), ('ace/mode/gcode', 'Gcode'), ('ace/mode/gherkin', 'Gherkin'), ('ace/mode/gitignore', 'Gitignore'), ('ace/mode/glsl', 'Glsl'), ('ace/mode/gobstones', 'Gobstones'), ('ace/mode/golang', 'Go'), ('ace/mode/groovy', 'Groovy'), ('ace/mode/haml', 'HAML'), ('ace/mode/handlebars', 'Handlebars'), ('ace/mode/haskell', 'Haskell'), ('ace/mode/haxe', 'haXe'), ('ace/mode/html', 'HTML'), ('ace/mode/html_elixir', 'HTML (Elixir)'), ('ace/mode/html_ruby', 'HTML (Ruby)'), ('ace/mode/ini', 'INI'), ('ace/mode/io', 'Io'), ('ace/mode/jack', 'Jack'), ('ace/mode/jade', 'Jade'), ('ace/mode/java', 'Java'), ('ace/mode/javascript', 'JavaScript'), ('ace/mode/json', 'JSON'), ('ace/mode/jsoniq', 'JSONiq'), ('ace/mode/jsp', 'JSP'), ('ace/mode/jsx', 'JSX'), ('ace/mode/julia', 'Julia'), ('ace/mode/latex', 'LaTeX'), ('ace/mode/lean', 'Lean'), ('ace/mode/less', 'LESS'), ('ace/mode/liquid', 'Liquid'), ('ace/mode/lisp', 'Lisp'), ('ace/mode/livescript', 'LiveScript'), ('ace/mode/logiql', 'LogiQL'), ('ace/mode/lsl', 'LSL'), ('ace/mode/lua', 'Lua'), ('ace/mode/luapage', 'LuaPage'), ('ace/mode/lucene', 'Lucene'), ('ace/mode/makefile', 'Makefile'), ('ace/mode/markdown', 'Markdown'), ('ace/mode/mask', 'Mask'), ('ace/mode/matlab', 'MATLAB'), ('ace/mode/maze', 'Maze'), ('ace/mode/mel', 'MEL'), ('ace/mode/mushcode', 'MUSHCode'), ('ace/mode/mysql', 'MySQL'), ('ace/mode/nix', 'Nix'), ('ace/mode/nsis', 'NSIS'), ('ace/mode/objectivec', 'Objective-C'), ('ace/mode/ocaml', 'OCaml'), ('ace/mode/pascal', 'Pascal'), ('ace/mode/perl', 'Perl'), ('ace/mode/pgsql', 'pgSQL'), ('ace/mode/php', 'PHP'), ('ace/mode/powershell', 'Powershell'), ('ace/mode/praat', 'Praat'), ('ace/mode/prolog', 'Prolog'), ('ace/mode/properties', 'Properties'), ('ace/mode/protobuf', 'Protobuf'), ('ace/mode/python', 'Python'), ('ace/mode/r', 'R'), ('ace/mode/razor', 'Razor'), ('ace/mode/rdoc', 'RDoc'), ('ace/mode/rhtml', 'RHTML'), ('ace/mode/rst', 'RST'), ('ace/mode/ruby', 'Ruby'), ('ace/mode/rust', 'Rust'), ('ace/mode/sass', 'SASS'), ('ace/mode/scad', 'SCAD'), ('ace/mode/scala', 'Scala'), ('ace/mode/scheme', 'Scheme'), ('ace/mode/scss', 'SCSS'), ('ace/mode/sh', 'SH'), ('ace/mode/sjs', 'SJS'), ('ace/mode/smarty', 'Smarty'), ('ace/mode/snippets', 'snippets'), ('ace/mode/soy_template', 'Soy Template'), ('ace/mode/space', 'Space'), ('ace/mode/sql', 'SQL'), ('ace/mode/sqlserver', 'SQLServer'), ('ace/mode/stylus', 'Stylus'), ('ace/mode/svg', 'SVG'), ('ace/mode/swift', 'Swift'), ('ace/mode/tcl', 'Tcl'), ('ace/mode/tex', 'Tex'), ('ace/mode/text', 'Text'), ('ace/mode/textile', 'Textile'), ('ace/mode/toml', 'Toml'), ('ace/mode/twig', 'Twig'), ('ace/mode/typescript', 'Typescript'), ('ace/mode/vala', 'Vala'), ('ace/mode/vbscript', 'VBScript'), ('ace/mode/velocity', 'Velocity'), ('ace/mode/verilog', 'Verilog'), ('ace/mode/vhdl', 'VHDL'), ('ace/mode/wollok', 'Wollok'), ('ace/mode/xml', 'XML'), ('ace/mode/xquery', 'XQuery'), ('ace/mode/yaml', 'YAML')])), ('source', codeschool.blocks.ace.AceBlock())))), ('markdown', wagtailmarkdown.blocks.MarkdownBlock())), blank=True, help_text='This field should contain a text with any instructions, tips, or information that is relevant to the current quiz. Rembember to explain clearly the rules and what is expected from each student.', null=True, verbose_name='Quiz description')),
                ('grading_method', models.ForeignKey(blank=True, default=cs_core.models.activity.response_context.grading_method_best, help_text='Choose the strategy for grading this activity.', on_delete=django.db.models.deletion.SET_DEFAULT, to='cs_core.GradingMethod')),
                ('language', models.ForeignKey(blank=True, help_text='Forces an specific programming language for all programing-related questions. If not given, will accept responses in any programming language.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quizzes', to='cs_core.ProgrammingLanguage', verbose_name='Programming language')),
            ],
            options={
                'verbose_name_plural': 'quiz activities',
                'verbose_name': 'quiz activity',
            },
            bases=(codeschool.models.mixins.CopyMixin, codeschool.models.wagtail.CodeschoolPageMixin, codeschool.models.mixins.MigrateMixin, 'wagtailcore.page'),
        ),
        migrations.CreateModel(
            name='QuizItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('weight', models.FloatField(default=1.0, help_text='The non-normalized weight of this item in the total quiz grade.', verbose_name='value')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(codeschool.models.mixins.MigrateMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SimpleQuestion',
            fields=[
                ('page_ptr', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='simplequestion_instance', serialize=False, to='wagtailcore.Page')),
                ('content_color', models.CharField(default='#10A2A4', help_text='Personalize the main color for page content.', max_length=20, verbose_name='color')),
                ('short_description', models.CharField(blank=True, help_text='A very brief one-phrase description used in listings.', max_length=140, verbose_name='short description')),
                ('icon_src', models.CharField(blank=True, help_text='Optional icon name that can be used to personalize the activity. Material icons are available by using the "material:" namespace as in "material:menu".', max_length=50, verbose_name='activity icon')),
                ('resources', wagtail.wagtailcore.fields.StreamField((('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('embed', wagtail.wagtailembeds.blocks.EmbedBlock()), ('markdown', wagtailmarkdown.blocks.MarkdownBlock()), ('url', wagtail.wagtailcore.blocks.URLBlock()), ('text', wagtail.wagtailcore.blocks.TextBlock()), ('char', wagtail.wagtailcore.blocks.CharBlock()), ('ace', codeschool.blocks.ace.AceBlock()), ('bool', wagtail.wagtailcore.blocks.BooleanBlock()), ('doc', wagtail.wagtaildocs.blocks.DocumentChooserBlock()), ('snippet', wagtail.wagtailsnippets.blocks.SnippetChooserBlock(cs_core.models.activity.grading_method.GradingMethod)), ('date', wagtail.wagtailcore.blocks.DateBlock()), ('time', wagtail.wagtailcore.blocks.TimeBlock()), ('stream', wagtail.wagtailcore.blocks.StreamBlock((('page', wagtail.wagtailcore.blocks.PageChooserBlock()), ('html', wagtail.wagtailcore.blocks.RawHTMLBlock()))))))),
                ('stem', wagtail.wagtailcore.fields.StreamField((('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('heading', wagtail.wagtailcore.blocks.CharBlock(classname='full title')), ('code', wagtail.wagtailcore.blocks.StructBlock((('language', wagtail.wagtailcore.blocks.ChoiceBlock(choices=[('ace/mode/abap', 'ABAP'), ('ace/mode/abc', 'ABC'), ('ace/mode/actionscript', 'ActionScript'), ('ace/mode/ada', 'ADA'), ('ace/mode/apache_conf', 'Apache Conf'), ('ace/mode/asciidoc', 'AsciiDoc'), ('ace/mode/assembly_x86', 'Assembly x86'), ('ace/mode/autohotkey', 'AutoHotKey'), ('ace/mode/batchfile', 'BatchFile'), ('ace/mode/c_cpp', 'C and C++'), ('ace/mode/c9search', 'C9Search'), ('ace/mode/cirru', 'Cirru'), ('ace/mode/clojure', 'Clojure'), ('ace/mode/cobol', 'Cobol'), ('ace/mode/coffee', 'CoffeeScript'), ('ace/mode/coldfusion', 'ColdFusion'), ('ace/mode/csharp', 'C#'), ('ace/mode/css', 'CSS'), ('ace/mode/curly', 'Curly'), ('ace/mode/d', 'D'), ('ace/mode/dart', 'Dart'), ('ace/mode/diff', 'Diff'), ('ace/mode/django', 'Django'), ('ace/mode/dockerfile', 'Dockerfile'), ('ace/mode/dot', 'Dot'), ('ace/mode/dummy', 'Dummy'), ('ace/mode/dummysyntax', 'DummySyntax'), ('ace/mode/eiffel', 'Eiffel'), ('ace/mode/ejs', 'EJS'), ('ace/mode/elixir', 'Elixir'), ('ace/mode/elm', 'Elm'), ('ace/mode/erlang', 'Erlang'), ('ace/mode/forth', 'Forth'), ('ace/mode/ftl', 'FreeMarker'), ('ace/mode/gcode', 'Gcode'), ('ace/mode/gherkin', 'Gherkin'), ('ace/mode/gitignore', 'Gitignore'), ('ace/mode/glsl', 'Glsl'), ('ace/mode/gobstones', 'Gobstones'), ('ace/mode/golang', 'Go'), ('ace/mode/groovy', 'Groovy'), ('ace/mode/haml', 'HAML'), ('ace/mode/handlebars', 'Handlebars'), ('ace/mode/haskell', 'Haskell'), ('ace/mode/haxe', 'haXe'), ('ace/mode/html', 'HTML'), ('ace/mode/html_elixir', 'HTML (Elixir)'), ('ace/mode/html_ruby', 'HTML (Ruby)'), ('ace/mode/ini', 'INI'), ('ace/mode/io', 'Io'), ('ace/mode/jack', 'Jack'), ('ace/mode/jade', 'Jade'), ('ace/mode/java', 'Java'), ('ace/mode/javascript', 'JavaScript'), ('ace/mode/json', 'JSON'), ('ace/mode/jsoniq', 'JSONiq'), ('ace/mode/jsp', 'JSP'), ('ace/mode/jsx', 'JSX'), ('ace/mode/julia', 'Julia'), ('ace/mode/latex', 'LaTeX'), ('ace/mode/lean', 'Lean'), ('ace/mode/less', 'LESS'), ('ace/mode/liquid', 'Liquid'), ('ace/mode/lisp', 'Lisp'), ('ace/mode/livescript', 'LiveScript'), ('ace/mode/logiql', 'LogiQL'), ('ace/mode/lsl', 'LSL'), ('ace/mode/lua', 'Lua'), ('ace/mode/luapage', 'LuaPage'), ('ace/mode/lucene', 'Lucene'), ('ace/mode/makefile', 'Makefile'), ('ace/mode/markdown', 'Markdown'), ('ace/mode/mask', 'Mask'), ('ace/mode/matlab', 'MATLAB'), ('ace/mode/maze', 'Maze'), ('ace/mode/mel', 'MEL'), ('ace/mode/mushcode', 'MUSHCode'), ('ace/mode/mysql', 'MySQL'), ('ace/mode/nix', 'Nix'), ('ace/mode/nsis', 'NSIS'), ('ace/mode/objectivec', 'Objective-C'), ('ace/mode/ocaml', 'OCaml'), ('ace/mode/pascal', 'Pascal'), ('ace/mode/perl', 'Perl'), ('ace/mode/pgsql', 'pgSQL'), ('ace/mode/php', 'PHP'), ('ace/mode/powershell', 'Powershell'), ('ace/mode/praat', 'Praat'), ('ace/mode/prolog', 'Prolog'), ('ace/mode/properties', 'Properties'), ('ace/mode/protobuf', 'Protobuf'), ('ace/mode/python', 'Python'), ('ace/mode/r', 'R'), ('ace/mode/razor', 'Razor'), ('ace/mode/rdoc', 'RDoc'), ('ace/mode/rhtml', 'RHTML'), ('ace/mode/rst', 'RST'), ('ace/mode/ruby', 'Ruby'), ('ace/mode/rust', 'Rust'), ('ace/mode/sass', 'SASS'), ('ace/mode/scad', 'SCAD'), ('ace/mode/scala', 'Scala'), ('ace/mode/scheme', 'Scheme'), ('ace/mode/scss', 'SCSS'), ('ace/mode/sh', 'SH'), ('ace/mode/sjs', 'SJS'), ('ace/mode/smarty', 'Smarty'), ('ace/mode/snippets', 'snippets'), ('ace/mode/soy_template', 'Soy Template'), ('ace/mode/space', 'Space'), ('ace/mode/sql', 'SQL'), ('ace/mode/sqlserver', 'SQLServer'), ('ace/mode/stylus', 'Stylus'), ('ace/mode/svg', 'SVG'), ('ace/mode/swift', 'Swift'), ('ace/mode/tcl', 'Tcl'), ('ace/mode/tex', 'Tex'), ('ace/mode/text', 'Text'), ('ace/mode/textile', 'Textile'), ('ace/mode/toml', 'Toml'), ('ace/mode/twig', 'Twig'), ('ace/mode/typescript', 'Typescript'), ('ace/mode/vala', 'Vala'), ('ace/mode/vbscript', 'VBScript'), ('ace/mode/velocity', 'Velocity'), ('ace/mode/verilog', 'Verilog'), ('ace/mode/vhdl', 'VHDL'), ('ace/mode/wollok', 'Wollok'), ('ace/mode/xml', 'XML'), ('ace/mode/xquery', 'XQuery'), ('ace/mode/yaml', 'YAML')])), ('source', codeschool.blocks.ace.AceBlock())))), ('markdown', wagtailmarkdown.blocks.MarkdownBlock())), blank=True, help_text='Describe what the question is asking and how should the students answer it as clearly as possible. Good questions should not be ambiguous.', null=True, verbose_name='Question description')),
                ('author_name', models.CharField(blank=True, help_text="The author's name, if not the same user as the question owner.", max_length=100, verbose_name="Author's name")),
                ('comments', wagtail.wagtailcore.fields.RichTextField(blank=True, help_text='(Optional) Any private information that you want to associate to the question page.', verbose_name='Comments')),
                ('body', wagtail.wagtailcore.fields.StreamField((('numeric', wagtail.wagtailcore.blocks.StructBlock((('name', wagtail.wagtailcore.blocks.CharBlock(help_text='A name used to display this field in forms.', max_legth=200, required=True)), ('value', codeschool.blocks.core.FloatBlock(default=1.0, help_text='Relative weight given to this answer in the question.')), ('answer', codeschool.blocks.core.DecimalBlock(help_text='The numerical value for the correct answer.', required=True)), ('tolerance', codeschool.blocks.core.DecimalBlock(default=0, help_text='Tolerance around the correct answer in which responses are still considered to be correct.'))))), ('boolean', wagtail.wagtailcore.blocks.StructBlock((('name', wagtail.wagtailcore.blocks.CharBlock(help_text='A name used to display this field in forms.', max_legth=200, required=True)), ('value', codeschool.blocks.core.FloatBlock(default=1.0, help_text='Relative weight given to this answer in the question.')), ('answer', wagtail.wagtailcore.blocks.BooleanBlock(help_text='Correct true/false answer.', required=True))))), ('string', wagtail.wagtailcore.blocks.StructBlock((('name', wagtail.wagtailcore.blocks.CharBlock(help_text='A name used to display this field in forms.', max_legth=200, required=True)), ('value', codeschool.blocks.core.FloatBlock(default=1.0, help_text='Relative weight given to this answer in the question.')), ('answer', wagtail.wagtailcore.blocks.TextBlock(help_text='String with the correct answer.', required=True)), ('case_sensitive', wagtail.wagtailcore.blocks.BooleanBlock(default=False, help_text='If true, the response will be sensitive to the case.')), ('use_regex', wagtail.wagtailcore.blocks.BooleanBlock(default=False, help_text='If true, the answer string is interpreted as a regular expression. A response is considered to be correct if it matches the regular expression. Remember to use both ^ and $ to match thebegining and the end of the string, if that is desired.'))))), ('date', wagtail.wagtailcore.blocks.StructBlock((('name', wagtail.wagtailcore.blocks.CharBlock(help_text='A name used to display this field in forms.', max_legth=200, required=True)), ('value', codeschool.blocks.core.FloatBlock(default=1.0, help_text='Relative weight given to this answer in the question.')), ('answer', wagtail.wagtailcore.blocks.DateBlock(help_text='Required date.', required=True))))), ('content', wagtail.wagtailcore.blocks.StreamBlock((('description', wagtail.wagtailcore.blocks.RichTextBlock()), ('code', wagtail.wagtailcore.blocks.StructBlock((('language', wagtail.wagtailcore.blocks.ChoiceBlock(choices=[('ace/mode/abap', 'ABAP'), ('ace/mode/abc', 'ABC'), ('ace/mode/actionscript', 'ActionScript'), ('ace/mode/ada', 'ADA'), ('ace/mode/apache_conf', 'Apache Conf'), ('ace/mode/asciidoc', 'AsciiDoc'), ('ace/mode/assembly_x86', 'Assembly x86'), ('ace/mode/autohotkey', 'AutoHotKey'), ('ace/mode/batchfile', 'BatchFile'), ('ace/mode/c_cpp', 'C and C++'), ('ace/mode/c9search', 'C9Search'), ('ace/mode/cirru', 'Cirru'), ('ace/mode/clojure', 'Clojure'), ('ace/mode/cobol', 'Cobol'), ('ace/mode/coffee', 'CoffeeScript'), ('ace/mode/coldfusion', 'ColdFusion'), ('ace/mode/csharp', 'C#'), ('ace/mode/css', 'CSS'), ('ace/mode/curly', 'Curly'), ('ace/mode/d', 'D'), ('ace/mode/dart', 'Dart'), ('ace/mode/diff', 'Diff'), ('ace/mode/django', 'Django'), ('ace/mode/dockerfile', 'Dockerfile'), ('ace/mode/dot', 'Dot'), ('ace/mode/dummy', 'Dummy'), ('ace/mode/dummysyntax', 'DummySyntax'), ('ace/mode/eiffel', 'Eiffel'), ('ace/mode/ejs', 'EJS'), ('ace/mode/elixir', 'Elixir'), ('ace/mode/elm', 'Elm'), ('ace/mode/erlang', 'Erlang'), ('ace/mode/forth', 'Forth'), ('ace/mode/ftl', 'FreeMarker'), ('ace/mode/gcode', 'Gcode'), ('ace/mode/gherkin', 'Gherkin'), ('ace/mode/gitignore', 'Gitignore'), ('ace/mode/glsl', 'Glsl'), ('ace/mode/gobstones', 'Gobstones'), ('ace/mode/golang', 'Go'), ('ace/mode/groovy', 'Groovy'), ('ace/mode/haml', 'HAML'), ('ace/mode/handlebars', 'Handlebars'), ('ace/mode/haskell', 'Haskell'), ('ace/mode/haxe', 'haXe'), ('ace/mode/html', 'HTML'), ('ace/mode/html_elixir', 'HTML (Elixir)'), ('ace/mode/html_ruby', 'HTML (Ruby)'), ('ace/mode/ini', 'INI'), ('ace/mode/io', 'Io'), ('ace/mode/jack', 'Jack'), ('ace/mode/jade', 'Jade'), ('ace/mode/java', 'Java'), ('ace/mode/javascript', 'JavaScript'), ('ace/mode/json', 'JSON'), ('ace/mode/jsoniq', 'JSONiq'), ('ace/mode/jsp', 'JSP'), ('ace/mode/jsx', 'JSX'), ('ace/mode/julia', 'Julia'), ('ace/mode/latex', 'LaTeX'), ('ace/mode/lean', 'Lean'), ('ace/mode/less', 'LESS'), ('ace/mode/liquid', 'Liquid'), ('ace/mode/lisp', 'Lisp'), ('ace/mode/livescript', 'LiveScript'), ('ace/mode/logiql', 'LogiQL'), ('ace/mode/lsl', 'LSL'), ('ace/mode/lua', 'Lua'), ('ace/mode/luapage', 'LuaPage'), ('ace/mode/lucene', 'Lucene'), ('ace/mode/makefile', 'Makefile'), ('ace/mode/markdown', 'Markdown'), ('ace/mode/mask', 'Mask'), ('ace/mode/matlab', 'MATLAB'), ('ace/mode/maze', 'Maze'), ('ace/mode/mel', 'MEL'), ('ace/mode/mushcode', 'MUSHCode'), ('ace/mode/mysql', 'MySQL'), ('ace/mode/nix', 'Nix'), ('ace/mode/nsis', 'NSIS'), ('ace/mode/objectivec', 'Objective-C'), ('ace/mode/ocaml', 'OCaml'), ('ace/mode/pascal', 'Pascal'), ('ace/mode/perl', 'Perl'), ('ace/mode/pgsql', 'pgSQL'), ('ace/mode/php', 'PHP'), ('ace/mode/powershell', 'Powershell'), ('ace/mode/praat', 'Praat'), ('ace/mode/prolog', 'Prolog'), ('ace/mode/properties', 'Properties'), ('ace/mode/protobuf', 'Protobuf'), ('ace/mode/python', 'Python'), ('ace/mode/r', 'R'), ('ace/mode/razor', 'Razor'), ('ace/mode/rdoc', 'RDoc'), ('ace/mode/rhtml', 'RHTML'), ('ace/mode/rst', 'RST'), ('ace/mode/ruby', 'Ruby'), ('ace/mode/rust', 'Rust'), ('ace/mode/sass', 'SASS'), ('ace/mode/scad', 'SCAD'), ('ace/mode/scala', 'Scala'), ('ace/mode/scheme', 'Scheme'), ('ace/mode/scss', 'SCSS'), ('ace/mode/sh', 'SH'), ('ace/mode/sjs', 'SJS'), ('ace/mode/smarty', 'Smarty'), ('ace/mode/snippets', 'snippets'), ('ace/mode/soy_template', 'Soy Template'), ('ace/mode/space', 'Space'), ('ace/mode/sql', 'SQL'), ('ace/mode/sqlserver', 'SQLServer'), ('ace/mode/stylus', 'Stylus'), ('ace/mode/svg', 'SVG'), ('ace/mode/swift', 'Swift'), ('ace/mode/tcl', 'Tcl'), ('ace/mode/tex', 'Tex'), ('ace/mode/text', 'Text'), ('ace/mode/textile', 'Textile'), ('ace/mode/toml', 'Toml'), ('ace/mode/twig', 'Twig'), ('ace/mode/typescript', 'Typescript'), ('ace/mode/vala', 'Vala'), ('ace/mode/vbscript', 'VBScript'), ('ace/mode/velocity', 'Velocity'), ('ace/mode/verilog', 'Verilog'), ('ace/mode/vhdl', 'VHDL'), ('ace/mode/wollok', 'Wollok'), ('ace/mode/xml', 'XML'), ('ace/mode/xquery', 'XQuery'), ('ace/mode/yaml', 'YAML')])), ('source', codeschool.blocks.ace.AceBlock())))), ('markdown', wagtailmarkdown.blocks.MarkdownBlock()), ('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('document', wagtail.wagtaildocs.blocks.DocumentChooserBlock()), ('page', wagtail.wagtailcore.blocks.PageChooserBlock()))))), help_text='You can insert different types of fields for the student answers. This works as a simple form that accepts any combination of thedifferent types of answer fields.', verbose_name='Fields')),
                ('grading_method', models.ForeignKey(blank=True, default=cs_core.models.activity.response_context.grading_method_best, help_text='Choose the strategy for grading this activity.', on_delete=django.db.models.deletion.SET_DEFAULT, to='cs_core.GradingMethod')),
            ],
            options={
                'permissions': (('download_question', 'Can download question files'),),
                'abstract': False,
            },
            bases=(wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin, codeschool.models.mixins.CopyMixin, codeschool.models.wagtail.CodeschoolPageMixin, codeschool.models.mixins.MigrateMixin, 'wagtailcore.page'),
        ),
        migrations.CreateModel(
            name='QuestionResponseItem',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('cs_core.responseitem',),
        ),
        migrations.CreateModel(
            name='QuizResponse',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(codeschool.models.mixins.MigrateMixin, 'cs_core.response'),
        ),
        migrations.AddField(
            model_name='quizitem',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.Page'),
        ),
        migrations.AddField(
            model_name='quizitem',
            name='quiz',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_items', to='cs_questions.Quiz'),
        ),
        migrations.AddField(
            model_name='answerkeyitem',
            name='question',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer_key_items', to='cs_questions.CodingIoQuestion'),
        ),
        migrations.CreateModel(
            name='CodingIoResponseItem',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(codeschool.models.mixins.MigrateMixin, 'cs_questions.questionresponseitem'),
        ),
        migrations.CreateModel(
            name='SimpleQuestionResponse',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=(codeschool.models.mixins.MigrateMixin, 'cs_questions.questionresponseitem'),
        ),
        migrations.AlterUniqueTogether(
            name='answerkeyitem',
            unique_together=set([('question', 'language')]),
        ),
    ]
