import functools
from typing import Any, Callable, Dict, Optional, Union
from contextlib import contextmanager, AbstractContextManager, ExitStack

from . import utils
from .validator import Validator, QvalValidationError
from . import exceptions
from . import framework_integration as fwk


class QueryParamValidator(AbstractContextManager):
    """
    Validates query parameters.

    Examples:
        >>> r = fwk.DummyRequest({"num": "42", "s": "str", "double": "3.14"})
        >>> params = QueryParamValidator(r, dict(num=int, s=None, double=float))
        >>> with params as p:
        ...     print(p.num, p.s, p.double, sep=', ')
        42, str, 3.14


    .. automethod:: __enter__
    .. automethod:: __exit__
    """

    def __init__(
        self,
        request: fwk.Request,
        factories: Dict[str, Optional[type]],
        validators: Dict[str, Validator.ValidatorType] = None,
        box_all: bool = True,
    ):
        """
        Instantiates the query validator.

        :param request: fwk.Request instance
        :param factories: mapping of :code:`{param -> factory}`. Providing :code:`None` as a factory is equivalent to :code:`str`
                       or :code:`lambda x: x`, since params are stored as strings.
        :param validators: dictionary of pre-defined validators
        :param box_all: include all params, even if they're not specified in :code:`factories`
        """
        self.request = request
        self._factories = factories
        self._box_all = box_all
        self._query_params = utils.get_request_params(self.request)

        self.result: Dict[str, Any] = {
            k: self.query_params[k]
            # Add all parameters to the resulting dictionary if box_all is true.
            # Otherwise keep only the specified parameters.
            for k in (self.query_params if self._box_all else self._factories)
        }
        self._params: Dict[str, Validator] = {k: Validator() for k in self.result}
        self._params.update(
            {
                # Convert predicates to validators
                k: Validator(v) if not isinstance(v, Validator) else v
                for k, v in (validators or {}).items()
            }
        )

    def apply_to_request(
        self, request: Union[Dict[str, str], fwk.Request]
    ) -> "QueryParamValidator":
        """
        Applies the current validation settings to a new request.

        Example:
            >>> from qval.utils import make_request
            >>> request = make_request({"a": "77"})
            >>> params = QueryParamValidator(request, {"a": int}, {"a": lambda x: x > 70})
            >>> with params as p:
            ...     print(p.a)  # Prints 77
            77
            >>> with params.apply_to_request({"a": "10"}): pass  # Error!
            Traceback (most recent call last):
                ...
            qval.exceptions.InvalidQueryParamException: ...

        :param request: new request instance
        :return: new :class:`QueryParamValidator` instance
        """
        return self.__class__(
            utils.make_request(request), self._factories, self._params, self._box_all
        )

    @property
    def query_params(self) -> Dict[str, str]:
        """
        Returns the dictionary of query parameters.
        """
        return self._query_params

    def add_predicate(self, param: str, predicate: Callable[[Any], bool]):
        """
        Adds a new check for the provided parameter.

        :param param: name of the request parameter
        :param predicate: predicate function
        :return: None
        """
        self._params.setdefault(param, Validator())
        self._params[param].add(predicate)

    # Alias for add_predicate; returns a reference to self
    def check(
        self, param: str, predicate: Callable[[Any], bool]
    ) -> "QueryParamValidator":
        """
        Adds a new check for the provided parameter.

        :param param: name of the request parameter
        :param predicate: predicate function
        :return: self
        """
        self.add_predicate(param, predicate)
        return self

    def positive(
        self, param: str, transform: Callable[[Any], Any] = lambda x: x
    ) -> "QueryParamValidator":
        """
        Adds the :code:`greater than zero` comparison check for the provided parameter.
        Provided :code:`param` will be tested as [:code:`transform(param) > 0`].

        :param param: name of the request parameter
        :param transform: callable that transforms the parameter, default: :code:`lambda x: x`
        :return: self
        """
        return self.check(param, lambda x: transform(x) >= 0)

    def gt(
        self, param: str, value: Any, transform: Callable[[Any], Any] = lambda x: x
    ) -> "QueryParamValidator":
        """
        Adds the :code:`greater than` comparison check for provided parameter.
        For example, if value = 10, :code:`param` will be tested as [:code:`transform(param) > 10`].

        :param param: name of the request parameter
        :param value: value to compare with
        :param transform: callable that transforms the parameter, default: :code:`lambda x: x`
        :return: self
        """
        return self.check(param, lambda x: transform(x) > value)

    def lt(
        self, param: str, value: Any, transform: Callable[[Any], Any] = lambda x: x
    ) -> "QueryParamValidator":
        """
        Adds the `less than` comparison check for the provided parameter.
        For example, if value = 10, :code:`param` will be tested as [:code:`transform(param) < 10`].

        :param param: name of the request parameter
        :param value: value to compare with
        :param transform: callable that transforms the parameter, default: :code:`lambda x: x`
        :return: self
        """
        return self.check(param, lambda x: transform(x) < value)

    def eq(
        self, param: str, value: Any, transform: Callable[[Any], Any] = lambda x: x
    ) -> "QueryParamValidator":
        """
        Adds the `equality` check for the provided parameter.
        For example, if value = 10, :code:`param` will be tested as [:code:`transform(param) == 10`].

        :param param: name of the request parameter
        :param value: value to compare with
        :param transform: callable that transforms the parameter, default: :code:`lambda x: x`
        :return: self
        """
        return self.check(param, lambda x: transform(x) == value)

    def nonzero(
        self, param: str, transform: Callable[[Any], Any] = lambda x: x
    ) -> "QueryParamValidator":
        """
        Adds the `nonzero` check for the provided parameter.
        For example, if value = 10, :code:`param` will be tested as [:code:`transform(param) != 0`].

        :param param: name of the request parameter
        :param transform: callable that transforms the parameter, default: :code:`lambda x: x`
        :return: self
        """
        return self.check(param, lambda x: transform(x) != 0)

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
        # Firstly, cast the parameters to required types
        for param, cast in self._factories.items():
            try:
                # If cast is None, just leave the parameter a string
                cast = cast or (lambda x: x)
                value = cast(self.query_params[param])
                self.result[param] = value
            except KeyError:
                raise exceptions.InvalidQueryParamException(
                    {"error": f"Missing required parameter `{param}`."},
                    status=fwk.HTTP_400_BAD_REQUEST,
                )
            # Invalid cast
            except (ValueError, TypeError):
                expected = "."
                # Expose only built-in types
                if cast in (int, float):
                    expected = f": expected {cast.__name__}."
                raise exceptions.InvalidQueryParamException(
                    {"error": f"Invalid type of the `{param}` parameter{expected}"},
                    status=fwk.HTTP_400_BAD_REQUEST,
                )

        # Run validations on each parameter
        for param, value in self.result.items():
            validator = self._params[param]
            try:
                if not validator(value):
                    raise QvalValidationError(
                        f"Invalid `{param}` value: {self.result[param]}."
                    )
            except QvalValidationError as e:
                raise exceptions.InvalidQueryParamException(
                    {"error": str(e)}, status=fwk.HTTP_400_BAD_REQUEST
                ) from e

    def __enter__(self) -> "utils.FrozenBox":
        """
        Runs validation on the provided request. See __exit__() for additional info.

        :return: box of validated values.
        """
        # This context manager will unwind stack in case of an error.
        # The __exit__() method will be called with values of the exception raised inside _validate().
        # This allows us to handle exceptions both inside _validate() and inside of the context.
        with self._cleanup_on_error():
            self._validate()
        return utils.FrozenBox(self.result)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        If occurred exception is not an :class:`InvalidQueryParamException <qval.exceptions.InvalidQueryParamException>`,
        the exception will be re-raised as an APIException, which will result in 500 error on the client side.

        :param exc_type: exception type
        :param exc_val: exception instance
        :param exc_tb: exception traceback
        :return: None
        """
        if exc_type not in (exceptions.InvalidQueryParamException, None):
            body = getattr(self.request, "body", {})
            text = (
                f"An error occurred during the validation or inside of the context: exc `{exc_type}` ({exc_val}).\n"
                f"| Parameters: {self.query_params}\n"
                f"| Body      : {body}\n"
                f"| Exception:\n"
            )
            utils.log.error(
                __name__,
                text,
                extra={
                    "stack": True,
                    "traceback": exc_tb,
                    "request_body": body,
                    "parameters": self.query_params,
                },
                exc_info=(exc_type, exc_val, exc_tb),
            )
            raise exceptions.APIException(
                detail="An error occurred while processing you request. "
                "Please contact the website administrator."
            ) from exc_val


def validate(
    request: Union[fwk.Request, Dict[str, str]],
    validators: Dict[str, Validator.ValidatorType] = None,
    box_all: bool = True,
    **factories,
) -> QueryParamValidator:
    """
    Shortcut for QueryParamValidator.

    Examples:
        >>> r = {"num": "42", "s": "str", "double": "3.14"}
        >>> with validate(r, num=int, s=None, double=float) as p:
        ...     print(p.num + p.double, p.s)
        45.14 str

        >>> r = {"price": "43.5$", "n_items": "1"}
        >>> currency2f = lambda x: float(x[:-1])
        >>> params = validate(r, price=currency2f, n_items=int
        ...     ).positive("n_items")  # n_items must be greater than 0
        >>> with params as p:
        ...     print(p.price, p.n_items)
        43.5 1

    :param request: request instance
    :param validators: dictionary of predefined validators
    :param box_all: include all params in the output dictionary, even if they're not specified in `factories`
    :param factories: factories that create python object from string parameters
    :return: QueryParamValidator instance
    """
    # Convert the request so it will matches the required request interface if needed
    request = utils.make_request(request)
    return QueryParamValidator(request, factories, validators, box_all)


def qval(
    factories: Dict[str, Optional[Callable[[str], Any]]],
    validators: Dict[str, Validator.ValidatorType] = None,
    box_all: bool = True,
    request_: fwk.Request = None,
):
    """
    A decorator that validates query parameters.
    The wrapped function must accept a request as the first argument
    (or second if it's a method) and `params` as last.

    :param factories: mapping (parameter, callable [str -> Any])
    :param validators: mapping (parameter, validator)
    :param box_all: include all params in the output dictionary, even if they're not specified in `factories`
    :param request_: optional request object will be always provided to the validator
    :return: wrapped function
    """
    # Check if the decorator is used improperly, i.e without `factories`
    if callable(factories):
        raise TypeError("qval() missing 1 required positional argument: 'factories'")

    def outer(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            args = list(args)
            # If a default request object is provided, simply use it
            if request_ is not None:
                request = utils.make_request(request_)
                args.insert(0, request)
            elif isinstance(args[0], fwk.RequestType):
                request = args[0] = utils.make_request(args[0])
            elif len(args) > 1 and isinstance(args[1], fwk.RequestType):
                request = args[1] = utils.make_request(args[1])
            else:
                raise ValueError(
                    "The first argument of the view must be a request-like."
                )
            with validate(request, validators, box_all, **factories) as params:
                return f(*args, params, **kwargs)

        return inner

    return outer


def qval_curry(request: fwk.Request):
    """
    Curries :func:`qval() <qval.qval.qval>` decorator and provides given :code:`request` object on each call.
    This is especially handy in Flask, where `request` is global.

    Example:
    .. code-block:: python

        >>> r = {"num": "42", "s": "str", "double": "3.14"}
        >>> qval = qval_curry(r)
        >>> @qval({"num": int, "double": float}, None)
        ... def view(request, extra_param, params):
        ...     print(params.num, params.double, params.s, extra_param, sep=', ')
        >>> view("test")
        42, 3.14, str, test

    :param request: request instance
    :return: wrapped :code:`qval(..., request_=request)`
    """

    @functools.wraps(qval)
    def outer(*args, **kwargs):
        kwargs.setdefault("request_", request)
        return qval(*args, **kwargs)

    return outer
