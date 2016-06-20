import os
from cs_core import models
from cs_core import factories
from django.core import serializers
base = os.path.dirname(__file__)

# Load users and profiles
fname = os.path.join(base, 'users-data.yaml')
with open(fname) as F:
    users = serializers.deserialize('yaml', F)
    for user in users:
        user.save()
        user.profile.about_me = 'Automatic user'
        user.profile.save()

# Load courses
with open('course-data.yaml') as F:
    data = F.read()
    #models.Course.load(data)