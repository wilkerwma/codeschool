from django.conf.urls import url, include
from cs_courses import views


def course_description(request, pk):
    course = get_object_or_404(models.Course, pk=pk)
    return http.HttpResponse(course.long_description_html)

urlpatterns = [
    url(r'^', views.CourseViewPack.as_include()),
]

