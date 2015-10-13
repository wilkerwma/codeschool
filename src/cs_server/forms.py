from django import forms
from cs_server.models import Student


class SubmitQuestionForm(forms.Form):

    '''Form used to insert answers in students responses.


    '''

    # First student
    name1 = forms.CharField(
        label='Nome/matrícula', max_length=200,
        error_messages={'required': 'Você deve registrar pelo menos um nome!'})
    school_id1 = forms.CharField(
        label='Matrícula', max_length=20,
        error_messages={'required': 'Digite a matrícula!'})

    # Second student
    name2 = forms.CharField(
        label='Nome/matrícula', max_length=200, required=False)
    school_id2 = forms.CharField(
        label='Matrícula', max_length=20, required=False)

    # Caixa de resposta
    response = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 25, 'name': 'code'}),
        initial='# Digite ou cole a sua solução aqui\n')

    def students(self):
        '''Iterates over all pairs of (name, school_id) for each filled
        student in the form'''

        if 'name1' in self.cleaned_data:
            yield self.cleaned_data['name1'], self.cleaned_data['school_id1']
        if 'name2' in self.cleaned_data:
            yield self.cleaned_data['name2'], self.cleaned_data['school_id2']

    def get_student_from_db(self):
        '''Return a list with 0, 1 or 2 Student objects in the form.

        Create corresponding student if not present in the database.'''

        st_list = []

        for (name, school_id) in self.students():
            if not name or not school_id:
                continue

            query = Student.objects.filter(name=name, school_id=school_id)
            if len(query) == 0:
                student = Student(name=name, school_id=school_id)
                student.save()
            elif len(query) == 1:
                student = query[0]
            else:
                raise RuntimeError('student name/school_id is not unique')

            st_list.append(student)

        return st_list


class GradesForm(forms.Form):
    school_id = forms.CharField(
        label='Matrícula', max_length=20,
        error_messages={'required': 'Digite a matrícula!'})
