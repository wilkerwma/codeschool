from django.db import models


class SrviceModelMixin:
    pass


class SrviceModel(SrviceModelMixin, models.Model):
    class Meta:
        abstract = True