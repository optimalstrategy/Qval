# coding: utf-8
import os
import signal
from subprocess import Popen

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
EX_DIR = os.path.join(BASE_DIR, "examples")


def execute(command: str) -> Popen:
    """
    Executes given command in the `examples` directory.

    :param command: command string
    :return: Popen instance
    """
    cmd = f"cd {EX_DIR} && {command}"
    proc = Popen(cmd, shell=True, preexec_fn=os.setsid)
    proc.exterminate = lambda: os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    return proc


def start_server(framework: str) -> Popen:
    """
    Starts server for the given framework.
    Supports django, flask and falcon at the moment.

    :param framework: framework name
    :return: opened process
    """
    cmd = f"PYTHONPATH={BASE_DIR}"
    if framework == "django":
        cmd = f"cd django-example && {cmd} python manage.py runserver localhost:8000"
    elif framework == "flask":
        cmd = f"{cmd} FLASK_APP=flask-example.py flask run --port=8000"
    elif framework == "falcon":
        cmd = f"{cmd} python falcon-example.py"
    else:
        raise ValueError(
            f"Unknown framework: {framework}, "
            f"expected `django`, `flask` or `falcon`."
        )
    return execute(cmd)
