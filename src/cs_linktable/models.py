from django.db import models


class Table(models.Model):
    name = models.CharField(max_length=140)


class Row(models.Model):
    table = models.ForeignKey(Table, related_name='rows')
    name = models.CharField(max_length=140)
    url = models.URLField()

