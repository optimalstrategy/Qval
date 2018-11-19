# coding: utf-8
import os
import signal
from subprocess import Popen, PIPE

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
EX_DIR = os.path.join(BASE_DIR, "examples")


# TODO: google how to do it properly
class SupervisorProxy(Popen):
    """
    Wrapper over the `Popen` class.
    Attempts to kill the process on `__delete__()` call.
    """
    def __del__(self, *args, **kwargs):
        """
        Kills the process.
        """
        super().__del__(*args, **kwargs)
        try:
            os.killpg(os.getpgid(self.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

    def __str__(self) -> str:
        return f'<Process: `{self.args}`'


def execute(command: str) -> Popen:
    """
    Executes given command in the `examples` directory.

    :param command: command string
    :return: Popen instance
    """
    cmd = f"cd {EX_DIR} && {command}"
    proc = SupervisorProxy(cmd, shell=True, stdout=PIPE, preexec_fn=os.setsid)
    return proc


def start_server(framework: str) -> Popen:
    """
    Starts server for the given framework.
    Supports django, flask and falcon at the moment.

    :param framework: framework name
    :return: SupervisorProxy object. Basically Popen,
    but kills the process at the end.
    """
    cmd = f"PYTHONPATH={BASE_DIR}"
    if framework == "django":
        cmd = f"cd django-example && {cmd} python manage.py runserver localhost:8000"
    elif framework == 'flask':
        cmd = f"{cmd} FLASK_APP=flask-example.py flask run --port=8000"
    elif framework == 'falcon':
        cmd = f"{cmd} python falcon-example.py"
    else:
        raise ValueError(f"Unknown framework: {framework}, "
                         f"expected `django`, `flask` or `falcon`")
    return execute(cmd)
