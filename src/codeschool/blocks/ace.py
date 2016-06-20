from collections import OrderedDict
from django.utils.functional import cached_property
from django import forms
from wagtail.wagtailcore import blocks

ACE_LANGUAGE_CHOICES = OrderedDict([
    ("ace/mode/abap", "ABAP"),
    ("ace/mode/abc", "ABC"),
    ("ace/mode/actionscript", "ActionScript"),
    ("ace/mode/ada", "ADA"),
    ("ace/mode/apache_conf", "Apache Conf"),
    ("ace/mode/asciidoc", "AsciiDoc"),
    ("ace/mode/assembly_x86", "Assembly x86"),
    ("ace/mode/autohotkey", "AutoHotKey"),
    ("ace/mode/batchfile", "BatchFile"),
    ("ace/mode/c_cpp", "C and C++"),
    ("ace/mode/c9search", "C9Search"),
    ("ace/mode/cirru", "Cirru"),
    ("ace/mode/clojure", "Clojure"),
    ("ace/mode/cobol", "Cobol"),
    ("ace/mode/coffee", "CoffeeScript"),
    ("ace/mode/coldfusion", "ColdFusion"),
    ("ace/mode/csharp", "C#"),
    ("ace/mode/css", "CSS"),
    ("ace/mode/curly", "Curly"),
    ("ace/mode/d", "D"),
    ("ace/mode/dart", "Dart"),
    ("ace/mode/diff", "Diff"),
    ("ace/mode/django", "Django"),
    ("ace/mode/dockerfile", "Dockerfile"),
    ("ace/mode/dot", "Dot"),
    ("ace/mode/dummy", "Dummy"),
    ("ace/mode/dummysyntax", "DummySyntax"),
    ("ace/mode/eiffel", "Eiffel"),
    ("ace/mode/ejs", "EJS"),
    ("ace/mode/elixir", "Elixir"),
    ("ace/mode/elm", "Elm"),
    ("ace/mode/erlang", "Erlang"),
    ("ace/mode/forth", "Forth"),
    ("ace/mode/ftl", "FreeMarker"),
    ("ace/mode/gcode", "Gcode"),
    ("ace/mode/gherkin", "Gherkin"),
    ("ace/mode/gitignore", "Gitignore"),
    ("ace/mode/glsl", "Glsl"),
    ("ace/mode/gobstones", "Gobstones"),
    ("ace/mode/golang", "Go"),
    ("ace/mode/groovy", "Groovy"),
    ("ace/mode/haml", "HAML"),
    ("ace/mode/handlebars", "Handlebars"),
    ("ace/mode/haskell", "Haskell"),
    ("ace/mode/haxe", "haXe"),
    ("ace/mode/html", "HTML"),
    ("ace/mode/html_elixir", "HTML (Elixir)"),
    ("ace/mode/html_ruby", "HTML (Ruby)"),
    ("ace/mode/ini", "INI"),
    ("ace/mode/io", "Io"),
    ("ace/mode/jack", "Jack"),
    ("ace/mode/jade", "Jade"),
    ("ace/mode/java", "Java"),
    ("ace/mode/javascript", "JavaScript"),
    ("ace/mode/json", "JSON"),
    ("ace/mode/jsoniq", "JSONiq"),
    ("ace/mode/jsp", "JSP"),
    ("ace/mode/jsx", "JSX"),
    ("ace/mode/julia", "Julia"),
    ("ace/mode/latex", "LaTeX"),
    ("ace/mode/lean", "Lean"),
    ("ace/mode/less", "LESS"),
    ("ace/mode/liquid", "Liquid"),
    ("ace/mode/lisp", "Lisp"),
    ("ace/mode/livescript", "LiveScript"),
    ("ace/mode/logiql", "LogiQL"),
    ("ace/mode/lsl", "LSL"),
    ("ace/mode/lua", "Lua"),
    ("ace/mode/luapage", "LuaPage"),
    ("ace/mode/lucene", "Lucene"),
    ("ace/mode/makefile", "Makefile"),
    ("ace/mode/markdown", "Markdown"),
    ("ace/mode/mask", "Mask"),
    ("ace/mode/matlab", "MATLAB"),
    ("ace/mode/maze", "Maze"),
    ("ace/mode/mel", "MEL"),
    ("ace/mode/mushcode", "MUSHCode"),
    ("ace/mode/mysql", "MySQL"),
    ("ace/mode/nix", "Nix"),
    ("ace/mode/nsis", "NSIS"),
    ("ace/mode/objectivec", "Objective-C"),
    ("ace/mode/ocaml", "OCaml"),
    ("ace/mode/pascal", "Pascal"),
    ("ace/mode/perl", "Perl"),
    ("ace/mode/pgsql", "pgSQL"),
    ("ace/mode/php", "PHP"),
    ("ace/mode/powershell", "Powershell"),
    ("ace/mode/praat", "Praat"),
    ("ace/mode/prolog", "Prolog"),
    ("ace/mode/properties", "Properties"),
    ("ace/mode/protobuf", "Protobuf"),
    ("ace/mode/python", "Python"),
    ("ace/mode/r", "R"),
    ("ace/mode/razor", "Razor"),
    ("ace/mode/rdoc", "RDoc"),
    ("ace/mode/rhtml", "RHTML"),
    ("ace/mode/rst", "RST"),
    ("ace/mode/ruby", "Ruby"),
    ("ace/mode/rust", "Rust"),
    ("ace/mode/sass", "SASS"),
    ("ace/mode/scad", "SCAD"),
    ("ace/mode/scala", "Scala"),
    ("ace/mode/scheme", "Scheme"),
    ("ace/mode/scss", "SCSS"),
    ("ace/mode/sh", "SH"),
    ("ace/mode/sjs", "SJS"),
    ("ace/mode/smarty", "Smarty"),
    ("ace/mode/snippets", "snippets"),
    ("ace/mode/soy_template", "Soy Template"),
    ("ace/mode/space", "Space"),
    ("ace/mode/sql", "SQL"),
    ("ace/mode/sqlserver", "SQLServer"),
    ("ace/mode/stylus", "Stylus"),
    ("ace/mode/svg", "SVG"),
    ("ace/mode/swift", "Swift"),
    ("ace/mode/tcl", "Tcl"),
    ("ace/mode/tex", "Tex"),
    ("ace/mode/text", "Text"),
    ("ace/mode/textile", "Textile"),
    ("ace/mode/toml", "Toml"),
    ("ace/mode/twig", "Twig"),
    ("ace/mode/typescript", "Typescript"),
    ("ace/mode/vala", "Vala"),
    ("ace/mode/vbscript", "VBScript"),
    ("ace/mode/velocity", "Velocity"),
    ("ace/mode/verilog", "Verilog"),
    ("ace/mode/vhdl", "VHDL"),
    ("ace/mode/wollok", "Wollok"),
    ("ace/mode/xml", "XML"),
    ("ace/mode/xquery", "XQuery"),
    ("ace/mode/yaml", "YAML"),
])


class AceBlock(blocks.TextBlock):
    """
    A text input block that uses the AceEditor instance.
    """
    attrs = {}

    @cached_property
    def field(self):
        field_kwargs = {'widget': AceWidget(mode='python')}
        field_kwargs.update(self.field_options)
        return forms.CharField(**field_kwargs)

    class Meta:
        icon = "code"

    class Media:
        html = (
            'components/ace-editor/ace-editor.html',
        )


class CodeBlock(blocks.StructBlock):
    """
    Code Highlighting Block
    """

    language = blocks.ChoiceBlock(
        required=True,
        choices=ACE_LANGUAGE_CHOICES.items(),
    )
    code = AceBlock()

    class Meta:
        icon = 'code'

    def render(self, value):
        src = value['code'].strip('\n')
        lang = value['language'].ref
        return '<ace-editor mode="%s" read-only>%s</ace-editor>' % (lang, src)
