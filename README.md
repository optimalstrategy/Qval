# Qval Query param validation library


### Installation
```bash
$ pip install qval
```

# Usage
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
    # Factories that will be used to convert parameters to python objects (callable[str, any] -> object).
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
    param a : int
    param b : int, nonzero
    param token : string, length = 12  # 
       
    Example: GET /api/divide?a=10&b=2&token=abcdefghijkl -> 200, {"answer": 5}
    """
    # Parameter validation occurs in the context manager.
    # If validation fails or user code throws an error, context manager
    # will raise InvalidQueryParamException or APIException respectively.
    # In Django, these exception will be processed and result 
    # in error codes (400 and 500) on the client side.
    params = (
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
// Browser:
{
  "answer": 2
}
```
Sending b = 0 to this endpoint will result in the following message on the client side:


<br>If you have a lot of parameters and custom validators, it's better to use the `qval()` decorator:
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

# Any function wrapped with `qval()` must accept request as 
# first or second argument, and parameters as last.
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

## Examples:
1. [Flask](examples/flask-example.py)
```bash
$ FLASK_APP=examples/flask-example.py flask run
```

## TODO:
1. Write docs
2. Add better error messages
3. Fix integration
