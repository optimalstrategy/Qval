# coding: utf-8
import time
import pytest

from tests.test_frameworks.common import start_server
from tests.test_frameworks.api_test_functions import *


# Common tests from `api_test_functions` will be ran the flask server
@pytest.mark.flask
@pytest.fixture(scope="module")
def server(request):
    print("Starting flask server...")
    proc = start_server("flask")
    request.addfinalizer(proc.exterminate)
    # Wait while server is setting up
    time.sleep(1)
    return proc
