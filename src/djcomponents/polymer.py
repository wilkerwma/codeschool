class PaperTabs(Widget):
    """
    Represents a paper-tab element.
    """

    def add_child(self, tab):
        if not isinstance(tab, Tab):
            name = type(tab).__name__
            raise TypeError(
                'PaperTabs element only accept Tab children, got %s' % name
            )
        super().add_child(tab)


class Tab(Widget):
    """
    A tab element in the paper-tab
    """

    def __init__(self, title, **kwargs):
        self.title = title
        super().__init__(**kwargs)


