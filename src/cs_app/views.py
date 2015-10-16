from decimal import Decimal
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from . import models
from . import forms
from . import util


# Alias
users = User.objects


#
# Web site accounts and login
#
def new_account(request):
    """Create a new account"""

    if request.method == 'POST':
        form = forms.NewAccountForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            if request.user.is_authenticated():
                auth.logout(request, request.user)

            try:            
                users.get(username=username)
                form.add_error('username', 'Usuário já existe')
            except User.DoesNotExist:
                user = users.create_user(username, email, password, 
                                                first_name=first_name,
                                                last_name=last_name)
                user.save()
                user = auth.authenticate(username=username, password=password)
                auth.login(request, user)
                return redirect('/') 
    else:
        form = forms.NewAccountForm()

    return render(request, 'cs_app/newaccount.html', {'form': form})


#
# Discipline related views
#
@login_required
def list_disciplines(request):
    """Renders a list of all disciplines"""

    user = request.user
    enrolled = user.disciplines.all() | user.owned_disciplines.all()
    enrolled = enrolled.distinct()
    latest = models.Discipline.objects.order_by('-timestamp')[:10]
    
    context = dict(enrolled=enrolled.order_by('name'),
                   available=sorted(latest, key=lambda x: x.name)
    )
    return render(request, 'cs_app/list_disciplines.html', context)


@login_required
def discipline_detail(request, pk):
    """Present the question_detail description and a form that is used to
    submit new
    responses."""

    context = dict(
        discipline=get_object_or_404(models.Discipline, pk=pk),
    )
    return render(request, 'cs_app/discipline_detail.html', context)


#
# Question related views
# 
@login_required
def list_questions(request):
    """Render a list of list_questions"""

    latest = models.Question.objects.order_by('-timestamp')[:10]
    context = dict(questions=latest,)
    return render(request, 'cs_app/list_questions.html', context)


@login_required
def question_detail(request, question_id):
    """Present the question description and a form that is used to submit new
    responses."""

    question = get_object_or_404(models.Question, pk=question_id)
    response = None

    if request.method == 'POST':
        form = forms.SubmitQuestionForm(request.POST)

        if form.is_valid():
            students = None
            data = form.cleaned_data
            partner_username = data['partner_username']
            
            try:
                if not partner_username:
                    raise User.DoesNotExist
                partner = users.get(username=partner_username)
                students = [request.user, partner]
            except User.DoesNotExist:
                if not partner_username:
                    students = [request.user]
                else:
                    form.add_error('partner_username', 'Usuário inválido')
        
            if students is not None:
                response = form.data['response']
                response = question.grade_response(response, 
                                                   timeout=0.5)
                response.save_as_team(students)
    else:
        form = forms.SubmitQuestionForm()

    context = dict(
        form=form,
        question=question,
        response=response,
    )
    return render(request, 'cs_app/question_detail.html', context)


@permission_required('cs_app.download_question')
def question_download(request, question_id):
    """Retrieves a question_detail as a text file that can be imported into
    the main application"""

    question_detail = get_object_or_404(models.Question, pk=question_id)
    data = question_detail.document_text()
    return HttpResponse(data, content_type='text/plain')


@permission_required('cs_app.create_question')
def question_upload(request, question_id):
    """Retrieves a question_detail as a text file that can be imported into
    the main
    application"""

    question_detail = get_object_or_404(models.Question, pk=question_id)
    data = question_detail.document_text()
    return HttpResponse(data, content_type='text/plain')


#
# Grade related views
#
@login_required
def grades_detail(request, partner=None):
    """Detail the grades for the current login"""
    
    # Regular table of questions for a single user
    responses = _get_user_responses(request.user, partner)
    user_grades = util.grades_per_question(responses)
    user_grades = util.dataframe_to_html(user_grades)

    # If superuser, show a table with all responses
    if request.user.has_perm('cs_app.see_all_responses'):
        responses = _get_all_responses(request.user)
        group_grades = util.grades_per_user(responses)
        group_grades = util.dataframe_to_html(group_grades)
    else:
        group_grades = None

    # Process template and return
    context = dict(
        group_grades = group_grades,
        user_grades=user_grades,
    )
    return render(request, 'cs_app/grades_detail.html', context)


@permission_required('cs_app.see_all_responses')
def grades_csv(request, partner=None):
    """Return a CSV with the grades"""

    responses = models.Response.objects.all()
    group_grades = util.grades_per_user(responses)
    data = group_grades.to_csv()
    return HttpResponse(data, content_type='text/plain')


@login_required
def grades_csv(request, partner=None):
    """Return a CSV with the grades for a user"""

    responses = _get_user_responses(request.user)
    group_grades = util.grades_per_question(responses)
    data = group_grades.to_csv()
    return HttpResponse(data, content_type='text/plain')


@permission_required('cs_app.see_all_responses')
def grades_all_csv(request, partner=None):
    """Return a CSV with the grades for all users"""

    responses = _get_all_responses(request.user)
    group_grades = util.grades_per_user(responses)
    data = group_grades.to_csv()
    return HttpResponse(data, content_type='text/plain')


def _get_user_responses(user, partner=None):
    # Return a list of all responses valid for a given user
    responses = user.response_set
    if partner:
        responses &= partner.response_set
    return responses.select_related('question')


def _get_all_responses(user):
    # Return a list of all responses that the given user can see (e.g., because
    # user is a teacher who is inspecting its students)
    return models.Response.objects.all()


#
# Quiz related views
#
def quiz_detail(request):
    pass