import io
import copy
import pprint
import collections
__all__ = ['pdict', 'Markio']


class pdict(collections.MutableMapping):
    """
    A dictionary that can look for data in a parent mapping.
    """

    def __init__(self, parent, *args, **kwds):
        self._data = dict(*args, **kwds)
        self._parent = parent

    def __getitem__(self, key):
        try:
            return self._data[key]
        except KeyError:
            return self._parent[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        try:
            del self._data[key]
        except KeyError:
            if key not in self._parent:
                raise

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        used = set()
        for k in self._data:
            used.add(k)
            yield k
        for k in self._parent:
            if k not in used:
                used.add(k)
                yield k

    def __str__(self):
        return str(dict(self))

    def owned(self):
        """Return a dictionary with a copy of all data that is owned by the
        default dict."""

        return dict(self._data)


class Markio:
    """
    Base node for the Markio AST.
    """
    class __Literal(str):
        """A string-like object whose repr() is equal to str()"""

        def __repr__(self):
            return str(self)

    _valid_attrs = {
        # Basic values
        'title', 'author', 'slug', 'tags', 'timeout', 'short_description',

        # Sections
        'description', 'example', 'tests',
    }

    def __init__(self, title=None, **kwds):
        parent = kwds.pop('parent', None)
        if parent is None:
            kwds['tags'] = dict(kwds.pop('tags', []))
        else:
            if 'tags' in kwds:
                kwds['tags'] = list(kwds['tags'])

        self.title = title
        self.__dict__.update(kwds)
        self.answer_key = {}
        self.placeholder = {None: None}
        self.translations = {}
        self.meta = {}
        self._parent =  parent

    def __getattr__(self, attr):
        if attr not in self._valid_attrs:
            raise AttributeError(attr)

        if self._parent is None:
            return None
        else:
            return getattr(self._parent, attr)

    def __getitem__(self, key):
        if key is None:
            return self
        try:
            return self.translations[key]
        except KeyError:
            self.translations[key] = out = Markio(parent=self)
            out.answer_key = pdict(self.answer_key)
            out.placeholder = pdict(self.placeholder)
            out.meta = pdict(self.meta)
            return out

    def __contains__(self, lang):
        return lang in self.translations

    def __iter__(self):
        return iter(self.translations)

    def add_meta(self, section, key, value):
        """Adds a key of meta information in the given section."""

        section = self.meta.setdefault(section, {})
        section[key] = value

    def add_answer_key(self, source, lang):
        """Adds a new answer key source for a given programming language
        lang."""

        self.answer_key[lang] = source

    def add_placeholder(self, source, lang=None, i18n=None):
        """Adds a new placeholder text for a given programming language
        lang. If i18n is given, it will add the placeholder in a translation
        section."""

        if i18n is None:
            self.placeholder[lang] = source
        else:
            self[i18n].add_placeholder(source, lang)

    def iter_translations(self, flatten=False, yield_root=True):
        """Iterate over all pairs of (lang, ast).

        `lang` is a string with a language code (e.g: ``"pt_BR"``) and the ast
        is a markio structure to that given language.

        If some field is not present in a translation, it will use the value
        defined in the parent structure. The translation hierarchy can be more
        than one level deep, in order to accommodate sub-translations like 'pt'
        and 'pt_BR'. If flatten is `True`, it will flatten the translation tree.

        By default, the first pair is always (None, self), unless
        ``yield_root=False``.
        """

        yield (None, self)
        for lang, tree in sorted(self.translations.items()):
            yield (lang, tree)

    def source(self):
        """Renders the source code equivalent to the markio structure."""

        # Title
        lines = [self.title, '=' * len(self.title), '']

        # Meta info
        for meta in ['author', 'slug', 'timeout']:
            value = getattr(self, meta)
            if value is not None:
                lines.append('    %s: %s' % (meta.title(), value))
        if self.tags:
            tag_data = ' '.join('#%s' % tag for tag in self.tags)
            lines.append('    Tags: %s' % tag_data)

        if self.short_description:
            lines.extend(['', self.short_description])

        # Description and examples
        for (lang, obj) in self.iter_translations():
            add_description = True
            add_example = True

            if lang is None and obj.description:
                lines.append('')
                title = 'Description'
            elif not obj.description or obj.description == self.description:
                add_description = False
            else:
                title = 'Description (%s)' % lang

            if add_description:
                lines.extend(['', title, '-' * len(title), '', obj.description])

            # Examples
            if lang is None and obj.example:
                title = 'Example'
            elif not obj.example or obj.example == self.example:
                add_example = False
            else:
                title = 'Example (%s)' % lang

            if add_example:
                lines.extend(['', title, '-' * len(title), '',
                              indent(obj.example)])

        # Tests
        if self.tests:
            lines.extend(['', 'Tests', '-----', '', indent(self.tests)])

        # Answer keys
        lines.append('')
        for comp_lang, source in sorted(self.answer_key.items()):
            title = 'Answer Key (%s)' % comp_lang
            source = indent(source)
            lines.extend(['', title, '-' * len(title), '', source])

        # Default placeholder, if it exists
        lines.append('')
        for lang, obj in self.iter_translations():
            placeholders = list(obj.placeholder)
            try:
                placeholders.remove(None)
            except ValueError:
                pass
            placeholders.sort()
            placeholders.insert(0, None)

            for comp_lang in placeholders:
                value = obj.placeholder[comp_lang]
                if not value:
                    continue
                value = indent(value)

                if lang is None and comp_lang is None:
                    lines.extend(['\nPlaceholder', '-' * 11, '', value])
                    continue

                if lang is None:
                    title = 'Placeholder (%s)' % comp_lang
                elif comp_lang is None:
                    title = 'Placeholder (%s)' % lang
                else:
                    title = 'Placeholder (%s, %s)' % (lang, comp_lang)

                if lang is None or value != self.placeholder.get(comp_lang, None):
                    lines.extend(['', title, '-' * len(title), '', value])

        # Finished collecting lines: return
        return '\n'.join(lines)

    def pprint(self, file=None, **kwds):
        """Pretty print Markio structure.

        See pformat() if you want the corresponding string representation."""

        data = pprint.pformat(self._json(), **kwds)
        print(data, file=file)

    def pformat(self, **kwds):
        """Return a pretty-print representation of the markio structure."""

        file = io.StringIO()
        self.pprint(file=file, **kwds)
        return file.getvalue()

    def _json(self):
        """JSON-like expansion of the AST.

        All linear node instances are expanded into dictionaries."""

        json = copy.deepcopy(dict(self.__dict__))
        del json['_parent']

        # Use real dicts even in children
        for k, v in json.items():
            if isinstance(v, pdict):
                json[k] = v.owned()

        # Filter null values
        json = {k: v for (k, v) in json.items() if v}

        if json['placeholder'].get(None, 0) is None:
            del json['placeholder'][None]

        if 'translations' in json:
            translations = json['translations']
            json['translations'] = {k: v._json() for (k, v) in translations.items()}

        return json

    def copy(self):
        """Return a deep copy of itself."""

        return copy.deepcopy(self)


def indent(txt):
    """Indent text with 4 spaces."""

    return '\n'.join(('    ' + x if x else '') for x in txt.splitlines())


if __name__ == '__main__':
    import doctest
    doctest.testmod()
