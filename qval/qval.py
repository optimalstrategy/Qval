import functools
from typing import Any, Callable, Dict, Optional, Union
from contextlib import contextmanager, AbstractContextManager, ExitStack

from .utils import FrozenBox, log, make_request
from .validator import Validator
from .exceptions import APIException, InvalidQueryParamException
from .drf_integration import HTTP_400_BAD_REQUEST, Request, DummyRequest


class QueryParamValidator(AbstractContextManager):
    """
    Validates query parameters.

    Examples:
    Note: see `validate()` for mor examples.
    >>> r = DummyRequest({"num": "42", "s": "str", "double": "3.14"})
    >>> params = QueryParamValidator(r, dict(num=int, s=None, double=float))
    >>> with params as p:
        ... print(p.num, p.s, p.double, sep=', ')
    42, str, 3.14
    """

    def __init__(
        self,
        request: Request,
        fields: Dict[str, Optional[type]],
        validators: Dict[str, Validator] = None,
        box_all: bool = True,
    ):
        """
        Instantiates validator object.

        :param request: Request instance
        :param fields: mapping of {param -> wanted type}. Providing none as wanted type is equivalent to str,
                       since params are stored as strings.
        :param validators: dictonary of pre-defined validators
        :param box_all: include all params that no specified in fields in the param box
        """
        self.request = request
        self.__fields = fields
        self._box_all = box_all
        self.result: Dict[str, Any] = {
            k: self.query_params[k]
            # Add all parameters to resulting dictionary of box_all is true.
            # Otherwise keep only specified parameters.
            for k in (self.query_params if self._box_all else self.__fields)
        }
        self.__params: Dict[str, Validator] = {k: Validator() for k in self.result}
        self.__params.update(validators or {})

    @property
    def query_params(self) -> Dict[str, str]:
        """
        Returns dictionary of query parameters.
        """
        return self.request.query_params

    def add_predicate(self, param: str, predicate: Callable[[Any], bool]):
        """
        Adds new check for provided parameter.

        :param param: name of the request parameter
        :param predicate: predicate function
        :return: None
        """
        if param not in self.__params:
            self.__params[param] = Validator()
        self.__params[param].add(predicate)

    # Alias for add_predicate; returns reference
    def check(
        self, param: str, predicate: Callable[[Any], bool]
    ) -> "QueryParamValidator":
        """
        Adds new check from provided parameter.

        :param param: name of the request parameter
        :param predicate: predicate function
        :return: self
        """
        self.add_predicate(param, predicate)
        return self

    def positive(self, param: str) -> "QueryParamValidator":
        """
        Adds `greater than zero` check for provided parameter.

        :param param: name of the request parameter
        :return: self
        """
        return self.check(param, lambda x: x > 0)

    def gt(
        self, param: str, value: Any, transform: Callable[[Any], Any] = lambda x: x
    ) -> "QueryParamValidator":
        """
        Adds `greater than` check for provided parameter.
        For example, if value = 10, parameter `param` would be tested as [transform(param) > 10].

        :param param: name of the request parameter
        :param value: value to compare with
        :param transform: callable that transforms the parameter, default: lambda x: x
        :return: self
        """
        return self.check(param, lambda x: transform(x) > value)

    def lt(
        self, param: str, value: Any, transform: Callable[[Any], Any] = lambda x: x
    ) -> "QueryParamValidator":
        """
        Adds `less than` check for provided parameter.
        For example, if value = 10, parameter `param` would be tested as [transform(param) < 10].

        :param param: name of the request parameter
        :param value: value to compare with
        :param transform: callable that transforms the parameter, default: lambda x: x
        :return: self
        """
        return self.check(param, lambda x: transform(x) < value)

    def eq(
        self, param: str, value: Any, transform: Callable[[Any], Any] = lambda x: x
    ) -> "QueryParamValidator":
        """
        Adds `equals` check for provided parameter.
        For example, if value = 10, parameter `param` would be tested as [transform(param) == 10].

        :param param: name of the request parameter
        :param value: value to compare with
        :param transform: callable that transforms the parameter, default: lambda x: x
        :return: self
        """
        return self.check(param, lambda x: transform(x) == value)

    @contextmanager
    def _cleanup_on_error(self):
        """
        Unwinds the stack in case of an error.
        """
        with ExitStack() as stack:
            stack.push(self)
            yield
            # The validation checks didn't raise an exception
            stack.pop_all()

    def _validate(self):
        """
        Validates the parameters.
        Only KeyError, ValueError and TypeError are handled as expected errors.
        :return: None
        """
        # Firstly cast parameters into required types
        for param, cast in self.__fields.items():
            try:
                # If cast is None, just leave parameter as a string
                cast = cast or (lambda x: x)
                value = cast(self.query_params[param])
                self.result[param] = value
            # Missing a required parameter
            except KeyError:
                raise InvalidQueryParamException(
                    {"error": f"Missing required parameter `{param}`."},
                    status=HTTP_400_BAD_REQUEST,
                )
            # Invalid cast
            except (ValueError, TypeError):
                expected = "."
                # Expose only built-in types
                print(cast)
                if cast in (int, float):
                    expected = f": expected {cast.__name__}."
                raise InvalidQueryParamException(
                    {"error": f"Invalid type of the `{param}` parameter{expected}"},
                    status=HTTP_400_BAD_REQUEST,
                )

        # Run validations on the each parameter
        for param, value in self.result.items():
            validator = self.__params[param]
            if not validator(value):
                raise InvalidQueryParamException(
                    {"error": f"Invalid `{param}` value: {self.result[param]}."},
                    status=HTTP_400_BAD_REQUEST,
                )

    def __enter__(self) -> "FrozenBox":
        """
        Runs validation on provided request. See __exit__() for additional info.
        :return: box of validated values.
        """
        # This context manager will unwind stack in case of an error.
        # The __exit__() method will be called with values of the exception raised inside _validate().
        # This allows us handle exceptions both inside _validate() and inside of the context.
        with self._cleanup_on_error():
            self._validate()
        return FrozenBox(self.result)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        If occurred exception is not an InvalidUriParamException, the exception would be re-raised as APIException,
        which will result in 500 error on the client side.

        :param exc_type: exception type
        :param exc_val: exception instance
        :param exc_tb: exception traceback
        :return:
        """
        # Report unexpected exceptions

        if exc_type not in (InvalidQueryParamException, None):
            text = f"An error occurred during the validation or inside of the context: exc `{exc_type}` (`{exc_val}`)."
            log.error(
                __name__,
                text,
                extra={
                    "stack": True,
                    "traceback": exc_tb,
                    "request_body": self.request.body,
                    "parameters": self.request.query_params,
                },
            )
            raise APIException(
                detail="An error occurred while processing you request. "
                "Please contact website administrator."
            ) from exc_val


def validate(
    request: Union[Request, Dict[str, str]],
    validators: Dict[str, Validator] = None,
    box_all: bool = True,
    **factories,
) -> QueryParamValidator:
    """
    Shortcut for QueryParamValidator.

    Examples:
    >>> r = {"num": "42", "s": "str", "double": "3.14"}
    >>> with validate(r, num=int, s=None, double=float) as p:
        ... print(p.num + p.double, p.s)
    45.14 s

    >>> r = {"price": "43.5$", "n_items": "1"}
    >>> currency2f = lambda x: float(x[:-1])
    >>> params = validate(r, price=currency2f, n_items=int
        ... ).positive("n_items")  # n_items must be greater than 0
    >>> with params as p:
        ... print(p.price, p.n_items)
    43.5 1

    :param request: request instance
    :param validators: dictionary of predefined validators
    :param box_all: include all params that no specified in factories in the param box
    :param factories: factories to validate
    :return: QueryParamValidator instance
    """
    # Wrap dictionary with request-like object
    if isinstance(request, dict):
        request = DummyRequest(request)
    return QueryParamValidator(request, factories, validators, box_all)


def qval(
    factories: Dict[str, Optional[Callable[[str], Any]]],
    validators: Dict[str, Validator] = None,
    box_all: bool = True,
):
    """
    A decorator that validates query parameters.
    The wrapped function must accept request as first parameter
    (or second if it's a method) and `params` as last.

    :param factories: mapping (parameter, callable [str -> Any])
    :param validators: mapping (parameter, validator)
    :param box_all: include all params that no specified in fields in the param box
    :return: wrapped function
    """
    # Check if decorator is used improperly
    if callable(factories):
        raise TypeError("qval() missing 1 required positional argument: 'factories'")

    def outer(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            args = list(args)
            if isinstance(args[0], (dict, Request)):
                request = args[0]
                # Construct request from dict
                args[0] = make_request(request)
            elif isinstance(args[1], (dict, Request)):
                request = args[1]
                args[1] = make_request(request)
            else:
                raise ValueError(
                    "The first argument of the view must be a request-like."
                )
            with validate(request, validators, box_all, **factories) as params:
                return f(*args, params, **kwargs)

        return inner

    return outer
