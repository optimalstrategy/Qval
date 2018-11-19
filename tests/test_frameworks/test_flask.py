# coding: utf-8
import time
import pytest

from test_frameworks.common import start_server
from test_frameworks.api_test_functions import *


# Common tests from api_test_function will be tested using flask app
@pytest.fixture(scope="module")
def server(request):
    """

    :param request: 

    """
    proc = start_server("flask")
    request.addfinalizer(proc.kill)
    # Wait while server is setting up
    time.sleep(0.3)
    return proc
