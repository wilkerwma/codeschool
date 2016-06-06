from djcomponents import TemplateWidget


class EditWidget(TemplateWidget):
    """
    Base class for widgets that perform an "Edit" action in a CRUD application.

    This widget creates a model form for editing the objects fields.
    """

    model = property(lambda x: type(x.object))

    def __init__(self, object, **kwargs):
        self.object = object
        super().__init__(**kwargs)

