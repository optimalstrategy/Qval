# coding: utf-8
import time
import pytest

from test_frameworks.common import start_server
from test_frameworks.api_test_functions import *


# Common tests from `api_test_functions` will be runned on the falcon server
@pytest.fixture(scope="module")
def server(request):
    print("Starting falcon server...")
    proc = start_server("falcon")
    request.addfinalizer(proc.exterminate)
    # Wait while server is setting up
    time.sleep(0.5)
    return proc
