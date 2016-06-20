from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import importlib


class Command(BaseCommand):
    help = 'loads required initial data for codeschool.'

    def add_arguments(self, parser):
        pass
        #parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for app in settings.INSTALLED_APPS:
            if app.startswith('cs_'):
                try:
                    mod = importlib.import_module(app + '.fixtures')
                except ImportError:
                    pass
                print(mod)