# Qval | Query param validation library


## Installation
```bash
$ pip install qval
```

## Basic usage
You can use Qval as both a function and a decorator. Function `validate()` accepts 3 positional arguments and 1 named:
```python
# qval.py
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
```
Imagine you have a RESTful calculator with an endpoint called `/api/divide`. You can use `validate()` 
to automatically convert parameters to python objects and then validate them:
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
    print(f"{params.item_id} costs {params.price}$.")
    ...
```

## Framework-specific instructions:
1. Django Rest Framework works straight out of the box. Simply add `@qval()` to your views or use `validate()` inside.

2. For Django _without_ DRF you may need to add exception handler to `settings.MIDDLEWARE`. Qval attempts to 
do it automatically if `DJANO_SETTINGS_MODULE` is set. Otherwise you'll see the following message:
    ```bash
    WARNING:root:Unable to add APIException middleware to the MIDDLEWARE list. Django does not 
    support APIException handling without DRF integration. Define DJANGO_SETTINGS_MODULE or 
    add 'qval.framework_integration.HandleAPIExceptionDjango' to the MIDDLEWARE list.
    ```
    Take a look at plain Django example [here](examples/django-example).

3. If you are using Flask, you will need to setup exception handlers:
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
    
    # Then use it as decorator.
    # Note: you view now must accept request as first argument
    @qval(...)
    def view(request, params): 
    ...
 
    ```
    Check out the full Flask [example](examples/flask-example.py) in `examples/flask-example.py`.<br>
    
    You can run the example using the command below:
    ```
    $ PYTHONPATH=. FLASK_APP=examples/flask-example.py flask run
    ```

4. Similarly to Flask, with Falcon you will need to setup error handlers:
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

## TODO:
1. Write docs
2. Add better error messages
