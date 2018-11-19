# coding: utf-8
import pytest

from test_frameworks.common import start_server
from test_frameworks.api_test_functions import *

# Common tests from api_test_function will be tested using flask server
@pytest.fixture
def server():
    return start_server("flask")
