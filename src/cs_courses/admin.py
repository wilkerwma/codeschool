from django.contrib import admin
from cs_courses import models


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    filter_horizontal = ('students',)
    list_filter = ('is_active', 'start')
    list_display = (
        'name',
        '_teacher_name',
        '_number_of_students',
        'start',
    )
    fieldsets = (
        (None, {
            'fields': ('discipline', 'teacher'),
        }),
        ('Alunos', {
            'classes': ('collapse',),
            'fields': ('students',),
        }),
        ('Ativação', {
            'classes': ('collapse',),
            'fields': ('is_active', 'start', 'end'),
        }),
        ('Descrição', {
            'classes': ('collapse',),
            'description': 'Estas opções permitem trocar a descrição padrão '
                           'na disciplina associada ao curso para uma descrição '
                           'personalizada específica para o curso em questão',
            'fields': ('short_description_override', 'long_description_override'),
        }),
    )
    save_as = True
    search_fields = (
        'discipline__name',
        'teacher__first_name',
        'teacher__last_name'
    )

    @staticmethod
    def _teacher_name(obj):
        teacher = obj.teacher
        return '%s %s' % (teacher.first_name, teacher.last_name)

    @staticmethod
    def _number_of_students(obj):
        return obj.students.count()


admin.site.register(models.Discipline)