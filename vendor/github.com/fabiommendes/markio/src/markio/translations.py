class Translation:
    """
    Stores a mapping of translations.


    Usage
    -----

    First, the translation object must be populated with translations

        >>> trans = Translation('pt_BR')
        >>> trans.add_translation('description', 'descrição')

    Call it to translate and normalize input strings:

        >>> trans('description')
        'descrição'
        >>> trans('Answer key')   # not in the dictionary!
        'answer_key'

    It also performs reverse translations

        >>> trans.en('descrição')
        'description'
    """

    def __init__(self, lang):
        self.lang = lang
        self._data = {}
        self._inv_data = {}

    @classmethod
    def fromstring(cls, lang, str):
        """Initialize translation from a string of definitions. It uses the
        format in the example bellow::

            # Lines starting with # are comments
            answer key = gabarito
            description = descrição
        """
        new = cls(lang)
        for line in str.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            en, _, trans = line.partition('=')
            if not trans:
                raise ValueError('invalid translation: %r' % line)
            new.add_translation(en, trans)
        return new

    def _normalize(self, st):
        return st.casefold().replace(' ', '_')

    def add_translation(self, english, transalated):
        """Adds a translation pair in the translations database."""

        english = self._normalize(english)
        transalated = self._normalize(transalated)
        self._data[english] = transalated
        self._inv_data[transalated] = english

    def en(self, text):
        """Reverse translation: from the foreign language back to english."""

        text = self._normalize(text)
        return self._inv_data.get(text, text)

    def copy(self, lang=None):
        """Return a copy of the translation object.

        If the user passes lang, the copy will have a different lang
        attribute."""

        new = object.__new__(Translation)
        new.lang = lang or self.lang
        new._data = self._data.copy()
        new._inv_data = self._inv_data.copy()
        return new

    def __call__(self, text):
        """Direct translation: from english to a foreign language."""

        text = self._normalize(text)
        return self._data.get(text, text)

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self.lang)


def get_translation(lang):
    """Return a translation object from the given language code."""

    lang = lang.casefold().replace('-', '_')
    try:
        return globals()[lang]
    except KeyError:
        return Translation(lang)

#
# Define translations
#
pt_br = Translation.fromstring('pt_BR', """
author = autor
timeout = tempo limite
short description = descrição curta
description = descrição
answer key = gabarito
""")

pt = pt_br.copy('pt')


