"""
This module provides convenient API for verifying query parameters.

The core class is called `QueryParamValidator`. It accepts 4 arguments:
- request: Request instance (Any object that has following attributes: GET, query_params and body)

- factories: Dictionary of factories {param -> factory}. The value of the parameter will be provided
  to factory before validation. Any callable that accepts string and returns anything is a valid factory.

- validators: Dictionary if validators {param -> Validator}. Validator is basically a list of predicates
  with the __call__() operator. See `Validator` class for more info.

- box_all: If true, adds all request parameter to the final result.
  Otherwise, only specified in `factories` parameters will be added.

If any parameter fails validation, `InvalidQueryParamException` (HTTP code = 400) will be raised.
Also, only `TypeError`, `ValueError` and `KeyError` occurred when param is provided to factory
result in the same exception.
Any error thrown inside or outside of the context will raise an APIError (HTTP code = 500).

Example:
    >>> from qval.framework_integration import DummyRequest
    >>> r = DummyRequest({"num": "42"})
    >>> with QueryParamValidator(r, {"num": int}) as p:
    ...     print(p.num)
    42

The code above is to verbose. That's why you should use `validator()` -
this function does the all boilerplate work for you:
    - `validator()` automatically converts dictionary to Request-like objects
    - Key-value arguments are used to provide factories
    - It's easier to type

    Simple example:
    >>> r = {"num": "42", "string": "s", "price": "3.14"}  # you can use dictionary instead of Request instance
    >>> with validate(r, num=int, price=float) as p:
    ...     print(p.num, p.price, p.string, sep=', ')
    42, 3.14, s

    A little bit more complex, with custom factory:
    >>> r = {"price": "2.79$", "tax": "0.5$"}
    >>> currency2f = lambda x: float(x[:-1])  # factory that converts {num}$ to float
    >>> with validate(r, price=currency2f, tax=currency2f) as p:
    ...     print(p.price, p.tax, sep=', ')
    2.79, 0.5


You can also use `qval()` decorator:
    >>> factories = {"num": int, "special": float}
    >>> validators = {"special": Validator(lambda x: x > 0)}
    >>> @qval(factories, validators)
    ... def view(request, params):  # class-based views are also supported
    ...     print(params.num, params.special, sep=", ")
    >>> view({"num": "10", "special": "0.7"})
    10, 0.7

    If something fails during validation or inside of the function, an error will be thrown.
    Consider the following examples:
    >>> factories = {"num": int, "special": int}  # now special is an integer
    >>> @qval(factories, validators=None)  # no validators for simplicity
    ... def view(request, params):
    ...     pass
    >>> view({"num": "10", "special": "0.7"})  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    qval.exceptions.InvalidQueryParamException:
        {'error': 'Invalid type of the `special` parameter: expected int.'}.

    The HTTP code of the exception above is 400 (Bad Request).

    Now the error is raised inside of the context block:
    >>> factories = {"num": int, "special": float}
    >>> @qval(factories, validators=None)  # no validators for simplicity
    ... def view(request, params):
    ...     raise IOError  # some random exception
    >>> view({"num": "10", "special": "0.7"})  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    qval.drf_integration.APIException: An error occurred while processing you request.
                                       Please contact website administrator.

    The HTTP code of the exception above is 500 (Internal Server Error).
    The error is logged to stdout by default. See the Note section for more info.

Notes:
    TODO: add notes
"""
from .utils import log
from .qval import QueryParamValidator, validate, qval, qval_curry
from .exceptions import InvalidQueryParamException, APIException
from .validator import Validator


__version__ = "0.1.6"
