================================
Welcome to Qval's documentation!
================================
`Qval <https://github.com/OptimalStrategy/qval>`_ is a query parameters validation library.
It is built using context managers and designed to work with
`Django Rest Framework <https://www.django-rest-framework.org/>`_, but also supports
`Django <https://www.djangoproject.com/>`_, `Flask <http://flask.pocoo.org/>`_ and
`Falcon <https://falconframework.org/>`_.

Qval can validate incoming query parameters, convert them to python objects and
automatically report errors to the client.

===========
Get started
===========
In order to use Qval in your project, install it with pip:

.. code-block:: bash

    $ pip install qval

===========
Basic usage
===========
Qval provides two ways of validation:

1. A function called :func:`validate() <qval.qval.validate>`:

    .. code-block:: python

        def validate(
            # Request instance. Must be a dictionary or support request interface.
            request: Union[Request, Dict[str, str]],
            # Dictionary of (param_name -> `Validator()` object).
            validators: Dict[str, Validator] = None,
            # Provide true if you want to access all parameters from the request through the context object.
            box_all: bool = True,
            # Factories that will be used to convert parameters to python objects (callable[str] -> object).
            **factories,
        ) -> QueryParamValidator:


2. A decorator called :func:`@qval() <qval.qval.qval>`:

    .. code-block:: python

        # Wrapped view must accept `request` as either first or second argument
        def qval(
            # Dictionary of (parameter -> factory or None)
            factories: Dict[str, Optional[Callable[[str], Any]]],
            # Dictionary of (parameter -> Validator)
            validators: Dict[str, Validator] = None,
            # Boxing flag. Provide True to access all provided parameters in the context manager
            box_all: bool = True,
            # Optional request instance that will be used to obtain query parameters
            request_: fwk.Request = None,
        ):


Let's jump to a quick example.
Imagine you have a RESTful calculator with an endpoint called :code:`/api/divide`. You can use :func:`validate() <qval.qval.validate>`
to automatically convert query parameters to python objects and then validate them:

    .. code-block:: python

        from qval import validate
        ...

        def division_view(request):
            """
            GET /api/divide?
            param a     : int
            param b     : int, nonzero
            param token : string, length = 12

            Example: GET /api/divide?a=10&b=2&token=abcdefghijkl -> 200, {"answer": 5}
            """
            # Parameter validation occurs in the context manager.
            # If validation fails or user code throws an error, context manager
            # will raise InvalidQueryParamException or APIException respectively.
            # In Django Rest Framework, these exceptions will be processed and result
            # in error codes (400 and 500) on the client side.
            params = (
                # `a` and `b` must be integers
                # Note: in order to get a nice error message on the client side,
                # you factory should raise either ValueError or TypeError
                validate(request, a=int, b=int)
                # `b` must be anything but zero
                .nonzero("b")
                # The `transform` callable will be applied to parameter before the check.
                # In this case we'll get `token`'s length and check if it is equal to 12.
                .eq("token", 12, transform=len)
            )
            # validation starts here
            with params as p:
                return Response({"answer": p.a // p.b})

    .. code-block:: javascript

        // GET /api/divide?a=10&b=2&token=abcdefghijkl
        // Browser:
        {
          "answer": 5
        }


    Sending :code:`b = 0` to this endpoint will result in the following message on the client side:

    .. code-block:: javascript

        // GET /api/divide?a=10&b=0&token=abcdefghijkl
        {
          "error": "Invalid `b` value: 0."
        }


If you have many parameters and custom validators, it's better to use the :func:`@qval() <qval.qval.qval>` decorator:

    .. code-block:: python

        # validators.py
        from decimal import Decimal
        from qval import Validator
        ...

        purchase_factories = {"price": Decimal, "item_id": int, "token": None}
        purchase_validators = {
            "price": Validator(lambda x: x > 0),
            "token": Validator(lambda x: len(x) == 12),
            "item_id": Validator(lambda x: x >= 0),
        }

        # views.py
        from qval import qval
        from validators import *
        ...

        # Any function or method wrapped with `qval()` must accept request as
        # either first or second argument, and parameters as last.
        @qval(purchase_factories, purchase_validators)
        def purchase_view(request, params):
            """
            GET /api/purchase?
            param item_id : int, positive
            param price   : float, greater than zero
            param token   : string, len == 12

            Example: GET /api/purchase?item_id=1&price=5.8&token=abcdefghijkl
            """
            # do something with p.item_id and p.price
            print(f"{params.item_id} costs {params.price}$.")
            ...

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
For Django _without_ DRF you may need to add exception handler to :code:`settings.MIDDLEWARE`. Qval attempts to
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


Full Falcon example can be `found <https://github.com/OptimalStrategy/qval/exmaples/falcon-example.py>`_
in the github repository.

Use the following command to run the app:

.. code-block:: bash

    $ PYTHONPATH=. python examples/falcon-example.py


===
API
===
:ref:`qval-api`

.. toctree::
   :maxdepth: 2
   :caption: Contents:
