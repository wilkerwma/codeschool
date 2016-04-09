from django.utils.translation import ugettext as __, ugettext_lazy as _
from codeschool import models
from codeschool.shortcuts import populate
from rest_framework import routers, viewsets, serializers


#
# REST framework
#
def rest_register(name, model=None):
    """A decorator that register a class into django's REST framework"""

    if model is None:
        def decorator(m):
            rest_register(name, m)
            return m
        return decorator

    if not isinstance(model, type):
        raise TypeError('invalid argument: %s, expect a type' % model)

    elif issubclass(model, models.Model):
        _model = model

        class ModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = _model
                fields = '__all__'

        class ModelViewSet(viewsets.ViewSet):
            queryset = _model.objects.all()
            serializer_class = ModelSerializer

        router.register(name, ModelViewSet)

    elif issubclass(model, viewsets.ViewSet):
        router.register(name, model)

    elif issubclass(model, serializers.BaseSerializer):
        class ModelViewSet(viewsets.ModelViewSet):
            queryset = model._meta.model.objects.all()
            serializer_class = model

        router.register(name, ModelViewSet)

    else:
        raise ValueError('bad type: %s' % model)


router = routers.DefaultRouter()


#
# Base models
#
@populate
class ProgrammingLanguage(models.Model):
    """Represents a programming language."""

    ref = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=140)
    comments = models.TextField(blank=True)

    @classmethod
    def populate(cls):
        setdefault = cls.setdefault

        # Python family
        setdefault(
            'python', 'Python 3.x', __('Default CPython interpreter'))
        setdefault(
            'python2', 'Python 2.7', __('Default CPython interpreter'))
        setdefault(
            'pytuga', 'Pytuguês', __('Default CPython interpreter'))

        # C family
        setdefault(
            'c', 'C99', __('C in GNU\'s compiler'))
        setdefault(
            'cpp', 'C++11', __('C in GNU\'s compiler'))

    @classmethod
    def setdefault(cls, ref, *args, **kwds):
        """Create object if it does not exists."""

        try:
            return cls.objects.get(ref=ref)
        except cls.DoesNotExists:
            return cls.create(ref, *args, **kwds)

    def __str__(self):
        return '%s (%s)' % (self.ref, self.name)


#
# why this duplication?
#
class ProgrammingLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammingLanguage
        fields = '__all__'


class ProgrammingLanguageViewSet(viewsets.ModelViewSet):
    queryset = ProgrammingLanguage.objects.all()
    serializer_class = ProgrammingLanguageSerializer

router.register(r'programming-language', ProgrammingLanguageViewSet)
