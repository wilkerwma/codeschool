from django.test import TestCase
import pytest
from . import models
# Create your tests here.

def action():
    return Action(12, 2, 222)

def test_action_creation(action):
    assert action.points == 12
    assert action.activity == 2
    assert action.user == 222
