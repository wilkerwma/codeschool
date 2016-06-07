from django.db import models
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