from django.contrib import admin
from .models import QuestionIO, Student, Answer, Grade

admin.site.register(QuestionIO)
admin.site.register(Student)
admin.site.register(Answer)
admin.site.register(Grade)
