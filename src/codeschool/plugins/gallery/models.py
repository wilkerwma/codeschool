from django.db import models
from django.contrib.auth.models import User
from model_utils.models import StatusModel, TimeFramedModel, TimeStampedModel


class Gallery(StatusModel, TimeFramedModel):
    name = models.CharField(max_length=140)
    description = models.TextField()


class Submission(TimeStampedModel):
    user = models.ForeignKmodeley(User)
    gallery = models.ForeignKey(Gallery)
    language = models.CharField(max_length=20)
    img = models.ImageField()
    code = models.TextField()

