from collections import OrderedDict
import warnings
import re
import configparser
import mistune
from markio.types import Markio
from markio.translations import Translation, get_translation
from markio.constants import (PROGRAMMING_LANGUAGES_CODES,
                              COUNTRY_CODES, LANGUAGE_CODES)

__all__ = ['parse', 'parse_string']
markdown = mistune.Markdown(escape=True)


def mistune_parse(source):
    """Use mistune to parse given source string."""

    return mistune.BlockLexer()(source)


def parse(file, extra=None):
    """
    Parse the given markio file.

    If it is a real file in the filesystem, the parser will look for
    supplementary data in adjacent files such as answer keys, lang files, etc.

    Args:
        file:
            A string with a path to a markio file or a file object.
        extra:
            A dictionary mapping fragment paths to files (or file paths) that
            hold that data.

    """

    if isinstance(file, str):
        with open(file) as F:
            return parse_string(F.read(), {})

    return parse_string(file.read(), {})


def parse_string(text, extra=None):
    """
    Like the :func:`markio.parse` function, but expects a string of text rather
    than a file object or the path to a file.
    """

    parser = Parser(text)
    return parser.parse()


def combine_keys(D, keytrans=lambda x: x, dict=OrderedDict):
    """Combine keys in a dictionary so section like 'foo (bar)' and 'foo (baz)'
    are merged into foo: {'bar': ..., 'baz': ...}.

    Parameters
    ----------

    D : mapping
        Input dictionary
    keytrans : callable
        Function that is applied to normalize the keys of the output dictionary.
    dict : type
        A callable that returns an empty mapping object. Useful, for instance
        if the user wants to return merged OrderedDict's rather than regular
        dictionaries.
    """
    out = dict()
    for (k, v) in D.items():
        k = k.strip()
        pre, sep, tail = k.partition('(')
        if sep:
            k = pre.strip()
            if tail[-1] != ')':
                raise SyntaxError('expect closing parenthesis')
            part = tail[:-1].strip()
        else:
            part = None
        dic = out.setdefault(keytrans(k), dict())
        dic[None if part is None else keytrans(part)] = v
    return out


def dom_flatten(dom_node, level=3):
    """Flatten dom node into a markdown source."""

    if isinstance(dom_node, list):
        data = []
        for node in dom_node:
            if node['type'] == 'code':
                code = '\n'.join('    ' + x for x in node['text'].splitlines())
                data.append(code)
            else:
                data.append(node['text'])
        return '\n\n'.join(data)
    else:
        data = []
        for title, content in dom_node.items():
            if title is not None:
                data.append('#' * level + ' ' + title)
            data.append(dom_flatten(content, level=level + 1))
        return '\n\n'.join(data)


def normalize_i18n(x):
    """Normalize accepted lang codes to ISO format.

    Also check if language codes are valid."""

    if x is None:
        return None
    return x.replace('-', '_')


def normalize_computer_language(x):
    """Normalize accepted computer language strings."""

    x = x.lower()
    return PROGRAMMING_LANGUAGES_CODES.get(x, x)


class Parser:
    """
    Represents a parsing job and is a function namespace.

    This class should not be used directly: please use the parse() and
    parse_string() functions.
    """
    def __init__(self, data):
        self.data = data
        self.markio = Markio()
        self.body = self.init_body()
        self.i18n = None
        self.trans = Translation('en')

    def parse(self):
        """
        Main entry point for the parsing job.
        """

        # Parse header
        self.parse_metadata()
        self.parse_short_description()

        # Combine sections with different i18n/programming language combinations
        # From this point we parse each section and include its contents in the
        # markio file
        self.sections = combine_keys(self.body, lambda x: x.lower())
        if self.i18n:
            to_english = self.trans.en
            items = self.sections.items()
            self.sections = {to_english(k): v for (k, v) in items}

        # Parse each section of the document
        self.parse_description()
        self.parse_tests()
        self.parse_answer_keys()
        self.parse_examples()
        self.parse_placeholders()

        if self.sections:
            # What should we do with additional sections? Probably we should
            # either issue an error or save them in some attribute of the markio
            # source. For now let us just ignore this problem.
            pass
        return self.markio

    def parse_metadata(self):
        """
        Process metadata block and save results in the markio object.
        """

        markio = self.markio

        # Meta-data is in an .ini block just under the main title.
        block = self.body.get(None, [])

        if block and block[0]['type'] == 'code':
            cfg = configparser.ConfigParser()

            # Before reading, we prepend data with the [DEFAULT] section that
            # is implicit in this block of data
            ini_data = block.pop(0)['text']
            ini_data = '[DEFAULT]\n' + ini_data
            cfg.read_string(ini_data)

            # Now we extract default data from this dictionary.
            cfg = {k: dict(v) for (k, v) in cfg.items()}
            default = cfg.pop('DEFAULT')

            # We check if internationalization is defined in the source file in
            # order to enable translation of strings
            if 'i18n' in cfg:
                self.trans = get_translation(cfg['i18n'])
                self.i18n = self.trans.lang
                to_english = self.trans.en

            # We convert all keys to english and translate simple keys
            cfg = {to_english(k): v for (k, v) in cfg}
            for key in ['author', 'slug']:
                value = default.pop(key, None)
                setattr(markio, key, value)

            # Some parameters require explicit parsing
            if 'timeout' in default:
                markio.timeout = self.parse_time(default.pop('timeout'))
            markio.tags = self.parse_tags(default.pop('tags', ''))

            # We prevent erroneous/invalid attributes in the default section
            if default:
                self.error(
                    'Invalid metadata attribute name in the DEFAULT section: %r'
                    % default.popitem()[0]
                )

            # The remaining sections are appended to a meta attribute. The user
            # can define any section she wants with any number of attributes.
            if cfg:
                markio.meta = cfg

            if default:
                key = next(iter(default))
                self.error('Invalid meta information: %r' % key)

    def parse_short_description(self):
        """
        Check if short description is available.
        """

        block = self.body.pop(None, [])
        if len(block) == 1:
            self.markio.short_description = block[0]['text']
        elif len(block) > 1:
            self.error(
                'Expects a single paragraph after metadata section'
            )

    def parse_tags(self, tags):
        """
        Parse a string and return the corresponding list of tags.
        """
        tags = tags.split()
        if not all(tag.startswith('#') for tag in tags):
            self.error('tags must start with an "#"')
        return [tag[1:] for tag in tags]

    def parse_time(self, st):
        """
        Parse a string that represents a time interval (e.g.: st = '1s') and
        return a float value representing this duration in seconds.
        """

        st = st.replace(' ', '').lower()
        try:
            return float(st)
        except ValueError:
            pass

        for ending, mul in [('second', 1), ('seconds', 1), ('sec', 1), ('s', 1),
                            ('minute', 60), ('minutes', 60), ('min', 60),
                            ('m', 60)]:
            if st.endswith(ending):
                try:
                    return float(st[:-len(ending)]) * mul
                except ValueError:
                    break
        self.error('invalid duration: %r' % st)

    def parse_description(self):
        """
        Parse the description section of the file.

        Search for internationalization.
        """

        descriptions = self.sections.pop('description', {})
        self.markio.description = dom_flatten(descriptions.get(None, []))
        for lang, descr in descriptions.items():
            lang = normalize_i18n(lang)
            self.markio[lang].description = dom_flatten(descr)

    def parse_tests(self):
        """Extract all test cases in iospec format.

        The "tests" section do not accept any translation or programming
        language specific data."""

        tests = self.sections.pop('tests', {})
        self.markio.tests = tests.pop(None, [{'text': ''}])[0]['text'].strip()
        if tests:
            test = next(iter(tests))
            self.error('invalid test subsection: Tests (%s)' % test)

    def parse_answer_keys(self):
        """Parse all answer key sections in the file.

        Answer keys do not accept internationalization, but require the
        specification of a programming language.
        """

        def get_code_block(k, x):
            return x[0]['text'].strip()

        if None in self.sections.get('answer key', {}):
            self.error('Must provide language for Answer Key')

        self.markio.answer_key.update({
            normalize_computer_language(k): get_code_block(k, v)
                for (k, v) in self.sections.pop('answer key', {}).items()
        })

    def parse_examples(self):
        """Parse the example section

        Example sections accept internationalization, but cannot be associated
        to programming languages."""

        markio = self.markio
        examples = self.sections.pop('example', {})
        markio.example = examples.get(None, [{'text': None}])[0]['text']
        if markio.example:
            markio.example = markio.example.strip()
        for lang, item in examples.items():
            lang = normalize_i18n(lang)
            markio[lang].example = item[0]['text'].strip()

    def parse_placeholders(self):
        """Extract all placeholder sections in file.

        Placeholders accept internationalization and can be associated to a
        programming language.
        """
        markio = self.markio

        # Extract placeholder information
        placeholders = self.sections.pop('placeholder', {})
        by_i18n = {None: {}}
        for k, v in placeholders.items():
            source = v[0]['text'].strip()

            if k is None:
                D = by_i18n[None]
                D[None] = source
            else:
                # Specify both programming language and i18n
                if ',' in k:
                    raise NotImplementedError('placeholder: %s' % k)

                else:
                    match = country_code_re.match(k)

                    # It is a lang/country code
                    if match and 0:
                        lang, country = match.groups()
                        if lang not in LANGUAGE_CODES:
                            warnings.warn("unsupported language code: %r" % lang)
                        if country not in COUNTRY_CODES:
                            warnings.warn("unsupported country code: %r" % country)

                        k = '%s-%s' % (lang, country.upper())
                        D = by_i18n.setdefault(k, {})
                        D[None] = source

                    # It is a programming language
                    else:
                        if k not in PROGRAMMING_LANGUAGES_CODES:
                            warnings.warn("unknown programming language: %r" % k)
                        D = by_i18n[None]
                        D[k] = source

        markio.placeholder = by_i18n.pop(None)
        for lang, item in by_i18n.items():
            lang = normalize_i18n(lang)
            markio[lang].placeholder = item.strip()

    def init_body(self):
        """
        Process mistune parse tree and make the dom node with a DOM-like
        hierarchy of sections in a tree structure. The title is saved in the
        markio object.

        The returned object is a dictionary of H2-level titles to their
        corresponding sub-ast's.
        """
        
        mistune_ast = mistune_parse(self.data)
        dom = self.make_dom(mistune_ast)
        del dom[None]

        # Verify if it starts with h1-level heading
        first_node = mistune_ast[0]
        if not(first_node['type'] == 'heading' and first_node['level'] == 1):
            self.error(
                'Document should start with a H1-level heading.'
            )
        if len(dom) != 1:
            print(self.data)
            print(mistune_ast)
            print(dom.keys())
            print(dom)
            self.error(
                'Only one H1-level title is allowed in the document.'
            )

        # Create return node
        title, dom = dom.popitem()
        self.markio.title = title
        return dom

    def make_dom(self, tree):
        """
        Process mistune parse tree and create an hierarchical DOM-like
        dictionary in which section names are keys and section contents are
        values.
        """

        current = []
        root = OrderedDict({None: current})
        levels = [D['level'] for D in tree if D['type'] == 'heading']
        if levels:
            level = min(levels)
        else:
            return tree

        for node in tree:
            if node['type'] == 'heading' and node['level'] == level:
                root[node['text']] = current = []
            else:
                current.append(node)

        return {k: self.make_dom(v) for (k, v) in root.items()}

    def error(self, msg):
        """Executed with an error message when syntax errors are found."""

        raise MarkioSyntaxError(msg)

#
# Re matches
#
country_code_re = re.compile(
    r'^\w*(?P<i18n>([a-zA-Z][a-zA-Z])((?:-|_)(:?[a-zA-Z][a-zA-Z]))?)\w*$')
parenthesis_re = re.compile(r'.*[(](.*)[)]\w*')


#
# Errors
#
class MarkioSyntaxError(SyntaxError):
    """Exception raised when syntax errors are found during parsing of a
    Markio source."""