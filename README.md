# Qval | Query params validation library
[![CircleCI](https://circleci.com/gh/OptimalStrategy/Qval/tree/master.svg?style=svg)](https://circleci.com/gh/OptimalStrategy/Qval/tree/master)
[![Documentation Status](https://readthedocs.org/projects/qval/badge/?version=latest)](https://qval.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/OptimalStrategy/Qval/branch/master/graph/badge.svg)](https://codecov.io/gh/OptimalStrategy/Qval)
[![PyPI version](https://badge.fury.io/py/qval.svg)](https://badge.fury.io/py/qval)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

* [Installation](#installation)
* [Basic usage](#basic-usage)
* [Framework-specific instructions](#framework-specific-instructions)
  * [Django Rest Framework](#drf)
  * [Plain Django](#plain-django)
  * [Flask](#flask)
  * [Falcon](#falcon)
* [Docs](#docs)
    * [Configuration](#configuration)
    * [Logging](#logging)

## About
Qval is a query parameters validation library designed to be used in small projects that require a lot of repetitive
parameter validation. In contrast with DRF's [Validators](https://www.django-rest-framework.org/api-guide/validators/)
(and other serialization abstractions), Qval requires almost no boilerplate.

## Installation
```bash
$ pip install qval
```

## Basic Usage
You can use Qval both as a function and decorator. The function `validate()` accepts 3 positional arguments and 1 named:
```python
# qval.py
def validate(
    # Request instance. Must implement the request interface or be a dictionary.
    request: Union[Request, Dict[str, str]],
    # A Dictionary in the form of (param_name -> `Validator()` object).
    validators: Dict[str, Validator] = None,
    # Provide true if you want to access any other parameters besides the configured ones  inside the validation context.
    box_all: bool = True,
    # The factories that will be used to convert the parameters to python objects..
    **factories: Optional[Callable[[str], object]],
) -> QueryParamValidator:
```

### A Use Case
Let's imagine that you have a RESTful calculator with an endpoint called `/api/divide`. You can use `validate()`
to automatically convert the parameters to python objects and then validate them:
```python
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
    # If validation fails or user code throws an error, the context manager
    # will raise InvalidQueryParamException or APIException respectively.
    # In Django Rest Framework, these exceptions will be processed and result
    # in the error codes 400 and 500 on the client side.
    params = (
        # `a` and `b` must be integers.
        # Note: in order to get a nice error message on the client side,
        # you factory should raise either ValueError or TypeError
        validate(request, a=int, b=int)
        # `b` must be anything but zero
        .nonzero("b")
        # The `transform` callable will be applied to the parameter before the check.
        # In this case we'll get `token`'s length and check if it is equal to 12.
        .eq("token", 12, transform=len)
    )
    # validation starts here
    with params as p:
        return Response({"answer": p.a // p.b})
```
```json
// GET /api/divide?a=10&b=2&token=abcdefghijkl
// Browser:
{
  "answer": 5
}
```
Sending b = 0 to this endpoint will result in the following message on the client side:
```json
// GET /api/divide?a=10&b=0&token=abcdefghijkl
{
  "error": "Invalid `b` value: 0."
}
```

<br>If you have many parameters and custom validators, it's better to use the `@qval()` decorator:
```python
# validators.py
from decimal import Decimal
from qval import Validator, QvalValidationError
...

def price_validator(price: int) -> bool:
    """
    A predicate to validate `price` query parameter.
    Provides custom error message.
    """
    if price <= 0:
        # If price does not match our requirements, we raise QvalValidationError() with a custom message.
        # This exception will be handled in the context manager and will be reraised
        # as InvalidQueryParamException() [HTTP 400].
        raise QvalValidationError(f"Price must be greater than zero, got \'{price}\'.")
    return True


purchase_factories = {"price": Decimal, "item_id": int, "token": None}
purchase_validators = {
    "token": Validator(lambda x: len(x) == 12),
    # Validator(p) can be omitted if there is only one predicate:
    "item_id": lambda x: x >= 0,
    "price": price_validator,
}

# views.py
from qval import qval
from validators import *
...

# Any function or method wrapped with `qval()` must accept `request` as
# either first or second argument, and `params` as last.
@qval(purchase_factories, purchase_validators)
def purchase_view(request, params):
    """
    GET /api/purchase?
    param item_id : int, positive
    param price   : float, greater than zero
    param token   : string, len == 12

    Example: GET /api/purchase?item_id=1&price=5.8&token=abcdefghijkl
    """
    print(f"{params.item_id} costs {params.price}$.")
    ...
```

## Framework-specific Instructions
1. <a name="drf"></a> Django Rest Framework works straight out of the box. Simply add `@qval()` to your views or use `validate()` inside.

2. <a name="plain-django"></a> For Django _without_ DRF you may need to add the exception handler to `settings.MIDDLEWARE`. Qval attempts to
do it automatically if `DJANO_SETTINGS_MODULE` is set. Otherwise you'll see the following message:
    ```bash
    WARNING:root:Unable to add the APIException middleware to the MIDDLEWARE list. Django does not
    support APIException handling without DRF integration. Define DJANGO_SETTINGS_MODULE or
    add 'qval.framework_integration.HandleAPIExceptionDjango' to the MIDDLEWARE list.
    ```
    Take a look at the plain Django example [here](examples/django-example).

3. <a name="flask"></a>If you are using Flask, you will need to setup the exception handlers:
    ```python
    from flask import Flask
    from qval.framework_integration import setup_flask_error_handlers
    ...
    app = Flask(__name__)
    setup_flask_error_handlers(app)
    ```
    Since `request` in Flask is a global object, you may want to curry `@qval()` before usage:
    ```python
    from flask import request
    from qval import qval_curry

    # Firstly, curry `qval()`
    qval = qval_curry(request)
    ...

    # Then use it as a decorator.
    # Note: you view now must accept `request` as its first argument
    @app.route(...)
    @qval(...)
    def view(request, params):
    ...

    ```
    Check out the full Flask [example](examples/flask-example.py) in `examples/flask-example.py`.<br>

    You can run the example using the command below:
    ```
    $ PYTHONPATH=. FLASK_APP=examples/flask-example.py flask run
    ```

4. <a name="falcon"></a>Similarly to Flask, with Falcon you will need to setup the error handlers:
    ```python
    import falcon
    from qval.framework_integration import setup_falcon_error_handlers
    ...
    app = falcon.API()
    setup_falcon_error_handlers(app)
    ```
    Full Falcon [example](examples/falcon-example.py) can be found here: `examples/falcon-example.py`.<br>

    Use the following command to run the app:
    ```
    $ PYTHONPATH=. python examples/falcon-example.py
    ```

## Docs
Refer to the [documentation](https://qval.rtfd.io) for more verbose descriptions and auto-generated API docs.
You can also look at the [tests](tests) to get a better idea of how the library works.

### Configuration
Qval supports configuration via python config files and environmental variables.
If `DJANGO_SETTINGS_MODULE` or `SETTINGS_MODULE` are defined, the specified config module will be used. Otherwise,
all lookups would be done in `os.environ`. <p>
Supported variables:
* `QVAL_MAKE_REQUEST_WRAPPER = myapp.myfile.my_func`. Customizes the behaviour of the `make_request()` function,
which is applied to all incoming requests, after which the result is passed to `qval.qval.QueryParamValidator`.
The provided function must accept `request` and return an object that supports the request interface
(see `qval.framework_integration.DummyReqiest`).
<br>For example, the following code adds logging to each `make_request()` call:

    ```python
    # app/utils.py
    def my_wrapper(f):
        @functools.wraps(f)
        def wrapper(request):
            print(f"Received new request: {request}")
            return f(request)
        return wrapper
    ```
    You will also need to execute `export QVAL_MAKE_REQUEST_WRAPPER=app.utils.my_wrapper` in your console
    or to add it to the config file.
* `QVAL_REQUEST_CLASS = path.to.CustomRequestClass`. `@qval()` will use it to determine which argument is the request.
If you have a custom request class that implements the `qval.framework_integration.DummyRequest` interface, provide it using this variable.

### Logging
Qval uses a global object called `log` for reporting errors. You disable this by calling `log.disable()`. Example error message:
```bash
An error occurred during the validation or inside of the context: exc `<class 'OverflowError'>` ((34, 'Numerical result out of range')).
| Parameters: <QueryDict: {'a': ['2.2324'], 'b': ['30000000']}>
| Body      : b''
| Exception:
Traceback (most recent call last):
  File "<path>/qval/qval.py", line 338, in inner
    return f(*args, params, **kwargs)
  File "<path>/examples/django-example/app/views.py", line 46, in pow_view
    return JsonResponse({"answer": params.a ** params.b})
OverflowError: (34, 'Numerical result out of range')
Internal Server Error: /api/pow
[19/Nov/2018 07:03:15] "GET /api/pow?a=2.2324&b=30000000 HTTP/1.1" 500 102
```

Disable logging with the following code:
```python
from qval import log
log.disable()
```
