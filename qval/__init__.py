"""
This module provides a convenient API for verifying query parameters.

The core class is called `QueryParamValidator`. It accepts 4 arguments:

- request: Request instance (Any object that has the following attributes: `GET`, `query_params`, `body`)

- factories: A dictionary of factories `{param -> factory}`. The value of the parameter will be provided
  to the factory before validation. Any callable that accepts a string and returns anything is a valid factory.

- validators: A dictionary of validators `{param -> Validator}`. A `Validator` is basically a list of predicates
  with `__call__`. See the `Validator` class for more info.

- box_all: If true, adds all request parameters to the output collection.
  Otherwise, only the parameters specified in `factories` will be added.

If any of the parameters fails validation, `InvalidQueryParamException` (HTTP code = 400) will be raised.
Only `TypeError`, `ValueError` and `KeyError` raised after the argument was provided to the factory
result in this exception.
Any error thrown inside or outside the context will raise an APIError (HTTP code = 500).

Example:
    >>> from qval.framework_integration import DummyRequest
    >>> r = DummyRequest({"num": "42"})
    >>> with QueryParamValidator(r, {"num": int}) as p:
    ...     print(p.num)
    42

The code above is too verbose to use if frequently. Instead, there is `validate()` --
this function does all the boilerplate work for you:
- `validate()` automatically converts dictionaries to Request-like objects
- Key-value arguments are used to provide factories
- It's easier to type

A simple example:
    >>> r = {"num": "42", "string": "s", "price": "3.14"}  # you can use a dictionary instead of a Request-like object
    >>> with validate(r, num=int, price=float) as p:
    ...     print(p.num, p.price, p.string, sep=', ')
    42, 3.14, s

A slightly more complex example, with a custom factory:
    >>> r = {"price": "2.79$", "tax": "0.5$"}
    >>> currency2f = lambda x: float(x[:-1])  # factory that converts {num}$ to float
    >>> with validate(r, price=currency2f, tax=currency2f) as p:
    ...     print(p.price, p.tax, sep=', ')
    2.79, 0.5


You can also use the `qval()` decorator:
    >>> factories = {"num": int, "special": float}
    >>> validators = {"special": Validator(lambda x: x > 0)}
    >>> @qval(factories, validators)
    ... def view(request, params):  # class-based views are also supported
    ...     print(params.num, params.special, sep=", ")
    >>> view({"num": "10", "special": "0.7"})
    10, 0.7

If something fails during the validation or inside the function, an error will be thrown.
Consider the following example:

    >>> factories = {"num": int, "special": int}  # now `special` is an integer
    >>> @qval(factories, validators=None)
    ... def view(request, params):
    ...     pass
    >>> view({"num": "10", "special": "0.7"})  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    qval.exceptions.InvalidQueryParamException:
        {'error': 'Invalid type of the `special` parameter: expected int.'}.

    The HTTP code of the exception above is 400 (Bad Request).

In case if an error is raised inside the context, an APIException will be generated:
    >>> factories = {"num": int, "special": float}
    >>> @qval(factories, validators=None)  # no validators for simplicity
    ... def view(request, params):
    ...     raise IOError  # some random exception
    >>> view({"num": "10", "special": "0.7"})  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    qval.framework_integration.APIException: An error occurred while processing you request.
                                             Please contact website administrator.

    The HTTP code of the exception above is 500 (Internal Server Error).
    The error is logged to stdout by default. See the Note section for more info.


Documentation:
    Refer to the documentation at https://qval.rtfd.io.
"""
from .utils import log
from .qval import QueryParamValidator, validate, qval, qval_curry
from .exceptions import InvalidQueryParamException, APIException
from .validator import Validator, QvalValidationError


__version__ = "0.4.2"
