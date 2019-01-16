===============================
Framework-specific instructions
===============================

---------------------
Django Rest Framework
---------------------
Django Rest Framework works straight out of the box. Simply add :func:`@qval() <qval.qval.qval>` to your views or
use :func:`validate() <qval.qval.validate>` inside.

------
Django
------
For Django *without* DRF you may need to add exception handler to :code:`settings.MIDDLEWARE`. Qval attempts to
do it automatically if :code:`DJANO_SETTINGS_MODULE` is set. Otherwise you'll see the following message:

.. code-block:: bash

    WARNING:root:Unable to add APIException middleware to the MIDDLEWARE list. Django does not
    support APIException handling without DRF integration. Define DJANGO_SETTINGS_MODULE or
    add 'qval.framework_integration.HandleAPIExceptionDjango' to the MIDDLEWARE list.


Take a look at the plain Django example `here <https://github.com/OptimalStrategy/Qval/tree/master/examples/django-example>`_.

-----
Flask
-----
If you are using Flask, you will need to setup exception handlers:

.. code-block:: python

    from flask import Flask
    from qval.framework_integration import setup_flask_error_handlers
    ...
    app = Flask(__name__)
    setup_flask_error_handlers(app)

Since :code:`request` in Flask is a global object, you may want to curry :func:`@qval() <qval.qval.qval>` before usage:

.. code-block:: python

    from flask import request
    from qval import qval_curry

    # Firstly, curry `qval()`
    qval = qval_curry(request)
    ...

    # Then use it as a decorator.
    # Note: you view now must accept request as first argument
    @app.route(...)
    @qval(...)
    def view(request, params):
    ...

Check out the full Flask `example <https://github.com/OptimalStrategy/Qval/tree/master/examples/flask-example.py>`_.
You can run the example using the command below:

.. code-block:: bash

    $ PYTHONPATH=. FLASK_APP=examples/flask-example.py flask run

------
Falcon
------
Similarly to Flask, with Falcon you will need to setup error handlers:

.. code-block:: python

    import falcon
    from qval.framework_integration import setup_falcon_error_handlers
    ...
    app = falcon.API()
    setup_falcon_error_handlers(app)


Full Falcon example can be `found <https://github.com/OptimalStrategy/Qval/tree/master/examples/falcon-example.py>`_
in the github repository.

Use the following command to run the app:

.. code-block:: bash

    $ PYTHONPATH=. python examples/falcon-example.py
