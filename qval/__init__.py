"""
This module convenient provides API to verify query parameters.

The core class is called `QueryParamValidator`. It accepts 4 arguments:
- request: Request instance (Any object that has following attributes: GET, query_params and body)

- factories: Dictionary of factories {param -> factory}. The value of the parameter will be provided
  to factory before validation. Any callable that accepts string and returns anything is a valid factory.

- validators: Dictionary if validators {param -> Validator}. Validator is basically a list of predicates
  with the __call__() operator. See `Validator` class for more info.

- box_all: If true, adds all request parameter to the final result.
  Otherwise, only specified in `factories` parameters will be added.


Examples:
    Using `validator()` wrapper:
      - `validator()` automatically converts dictionary to Request-like objects
      - Key-value arguments are used to provide factories

    >>> r = {"num": "42", "string": "s", "price": "3.14"}  # you can use dictionary instead of Request instance
    >>> with validate(r, num=int, price=float) as p:
        ... print(p.num, p.price, p.string)
    42 3.14 string
"""
from .utils import log
from .qval import QueryParamValidator, validate, qval
from .exceptions import InvalidQueryParamException, APIException
from .validator import Validator
