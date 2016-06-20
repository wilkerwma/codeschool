from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import importlib


class Command(BaseCommand):
    help = 'loads required initial data for codeschool.'

    def add_arguments(self, parser):
        parser.add_argument('--demo', '-d', action='store_true')

    def handle(self, *args, demo=False, **options):
        # Choose list of methods
        methods = ['initial']
        if demo:
            methods.append('demo')

        # Load data using each method
        for app in settings.INSTALLED_APPS:
            if app.startswith('cs_'):
                for method in methods:
                    try:
                        path = app + '.fixtures.' + method
                        mod = importlib.import_module(path)
                        print('Loaded data from %s.' % path)
                    except ImportError:
                        pass