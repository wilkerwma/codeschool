from decimal import Decimal
from codeschool.graders import PythonTemplate
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from cs_server.models import QuestionIO, Student, Answer
from cs_server.forms import SubmitQuestionForm, GradesForm

#
# Allow Pytuguese!
#
from pytuga import transpile
PythonTemplate.register_preprocessor('pytuga', transpile)


def index(request):
    '''Index page: render a list of questions'''

    latest = QuestionIO.objects.order_by('-pub_date')[:3]
    context = {'latest_list': latest}
    return render(request, 'cs_server/index.html', context)


def groupby(L, keyfunc):
    D = {}
    for x in L:
        key = keyfunc(x)
        try:
            D[key].append(x)
        except KeyError:
            D[key] = [x]
    return D


def grades_csv(resquest):
    answers = list(Answer.objects.all())
    by_st1 = groupby(answers, lambda x: getattr(x.student1, 'school_id', None))
    by_st2 = groupby(answers, lambda x: getattr(x.student2, 'school_id', None))
    by_st1.pop(None, None)
    by_st2.pop(None, None)

    students = {}
    for D in [by_st1, by_st2]:
        for k, v in D.items():
            k = k.replace('/', '')
            v = list(v)
            L = students.setdefault(k, [])
            L.extend(v)

    questions = set()
    for id_, answers in list(students.items()):
        answers = groupby(answers, lambda x: x.question)
        answers = {qst.id: (max(a.value for a in ans), len(ans))
                   for qst, ans in answers.items()}
        questions.update(answers)
        students[id_] = answers

    for answers in students.values():
        for question in questions:
            answers.setdefault(question, (Decimal(0), 0))

    questions = sorted(questions)
    data = ['#id; ' + '; '.join('%s; #' % QuestionIO.objects.get(pk=id_)
                                for id_ in questions)]
    for id_, responses in sorted(students.items()):
        line = [id_]
        for Q in questions:
            line.extend(responses[Q])
        data.append('; '.join(map(str, line)))

    data = '\n'.join(data).encode('latin1')
    return HttpResponse(
        data,
        content_type='text/plain')


def question(request, question_id):
    '''Present the question description and a form that is used to submit new
    responses.'''

    question = get_object_or_404(QuestionIO, pk=question_id)
    grade = None
    error_message = None

    if request.method == 'POST':
        form = SubmitQuestionForm(request.POST)

        if form.is_valid():
            # Grade response
            response = form.cleaned_data['response']
            grade, error_message = question.grade(response, timeout=0.5)

            # Save data on server
            students = form.get_student_from_db()
            save_response(question, response, grade, *students)
    else:
        form = SubmitQuestionForm()

    data = {
        'form': form,
        'question': question,
        'grade': grade,
        'error_message': error_message,
    }
    return render(request, 'cs_server/question.html', data)


def grades(request):
    grades = None

    if request.method == 'POST':
        form = GradesForm(request.POST)

        if form.is_valid():
            answers = []
            id_no = form.cleaned_data['school_id']
            students = Student.objects.filter(school_id=id_no)
            for st in students:
                answers.extend(st.answer_first.all())
                answers.extend(st.answer_second.all())

            # Get number of attempts and best grade
            grades = {}
            for ans in set(answers):
                try:
                    old_value, n_attempts = grades[ans.question]
                    if old_value < ans.value:
                        grades[ans.question] = (ans.value, n_attempts + 1)
                    else:
                        grades[ans.question] = (old_value, n_attempts + 1)
                except KeyError:
                    grades[ans.question] = (ans.value, 1)

            # Sort grades by question submited date
            grades = [(Q, value, N) for (Q, (value, N)) in grades.items()]
            grades.sort(key=lambda x: x[0].pub_date, reverse=True)
            grades = [(Q.title, value, N) for (Q, value, N) in grades]

    else:
        form = GradesForm()

    return render(request, 'cs_server/grades.html',
                  {'form': form, 'grades': grades})


def save_response(question, response, value, *students):
    '''Save a response from a question form'''
    # TODO: refactor this!

    # Create the answer object
    if len(students) == 1:
        answer = Answer(
            student1=students[0],
            question=question,
            response=response,
            value=value)
    elif len(students) == 2:
        answer = Answer(
            student1=students[0],
            student2=students[1],
            question=question,
            response=response,
            value=value)
    else:
        raise RuntimeError
    answer.save()
