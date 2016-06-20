from django.forms.widgets import Media as Media, MEDIA_TYPES
from django.forms import widgets


#
# Monkey patch django's Media class to accept html imports
#
class MediaExtra:
    def __init__(self, media=None, inject_html=False, **kwargs):
        self._html = []
        self._inject_html = inject_html
        self._init(media, **kwargs)

    def render_html(self):
        return [
            format_html(
                '<link rel="import" href="{}">',
                self.absolute_path(path)
            ) for path in self._html
        ]

    def render_js(self):
        if self._inject_html:
            return self._render_js() + self.render_html()
        else:
            return self._render_js()

    def add_html(self, data):
        if data:
            for path in data:
                if path not in self._html:
                    self._html.append(path)

# Save reference to old init and render_js methods
Media._init = Media.__init__
Media._render_js = Media.render_js

# Update methods
Media.__init__ = MediaExtra.__init__
Media.render_js = MediaExtra.render_js
Media.render_html = MediaExtra.render_html
Media.add_html = MediaExtra.add_html

# Update media types
MEDIA_TYPES += ('html',)
widgets.MEDIA_TYPES = MEDIA_TYPES
