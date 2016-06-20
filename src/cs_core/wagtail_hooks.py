from django.utils.html import format_html
from wagtail.wagtailcore import hooks


@hooks.register('insert_global_admin_js')
def global_admin_js():
    static = '/static/'
    bower = '/static/bower_components/'
    return format_html(
        '<script src="{1}requirejs/require.js" data-main="{0}js/config.js"></script>\n'
        '<script src="{1}webcomponentsjs/webcomponents-lite.min.js"></script>\n'
        '<link rel="import" href="{0}components/main.min.html">\n'.format(
            static, bower
        )
    )