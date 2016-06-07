from django.apps import AppConfig


class CsQuestionsConfig(AppConfig):
    name = 'cs_questions'

    def ready(self):
        from cs_questions import models

        models.ProgrammingLanguage.autofill()