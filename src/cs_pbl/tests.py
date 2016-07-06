from django.test import TestCase
#import pytest
from . import models
#from codeschool.tests import *

# Create your tests here.

def action():
    return Action(1, 2, 3, 4,1, 'Acao')

def test_action_creation(action):
    assert action.points_tried == 1
