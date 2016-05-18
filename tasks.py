from invoke import run, task
import os
import sys
sys.path.insert(1, '%s/src' % (os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codeschool.settings")
print(sys.path)


@task
def configure():
    os.chdir('src')
    from django.core import management
    management.call_command('makemigrations')
    management.call_command('migrate')
    management.call_command('createsuperuser')


@task
def syncdb():
    os.chdir('src')
    from django.core import management
    management.call_command('makemigrations')
    management.call_command('migrate')


@task
def gunicorn(bind='localhost:8000', collectstatic=False):
    if collectstatic:
        run('python src/manage.py collectstatic')
    os.chdir('src')
    run('gunicorn codeschool.wsgi -b %s --workers 13 --name codeschool-server' % bind)
   
   
@task
def serve(collectstatic=True):
    if collectstatic:
        run('python src/manage.py collectstatic')
    os.chdir('src')
    run('gunicorn codeschool.wsgi -b unix:/tmp/gunicorn.sock --workers 13 --name codeschool-server')
