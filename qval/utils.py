import logging
from typing import Dict, Any, List, Callable, Union

from qval.framework_integration import load_symbol
from . import framework_integration as fwk


@fwk._make_request
def make_request(request: Union[Dict[str, str], fwk.Request]) -> fwk.RequestType:
    """
    Creates a :class:`qval.framework_integration.DummyRequest`
    if :code:`request` is a dictionary, and returns the :code:`request` itself otherwise.

    The behavior of this function can be customized with the
    :func:`@_make_request() <qval.framework_integration._make_request>` decorator.
    Provide the path to your wrapper using :code:`QVAL_MAKE_REQUEST_WRAPPER` in the settings file
    or set it as an environment variable. The wrapper function must accept :code:`request` as the parameter and
    return an object that implements the request interface.

    For example, the following code adds `print` to each call of the function:
    ::

        # app/utils.py
        def my_wrapper(f):
            @functools.wraps(f)
            def wrapper(request):
                print(f"Received new request: {request}")
                return f(request)
            return wrapper

    Then execute :code:`export QVAL_MAKE_REQUEST_WRAPPER=app.utils.my_wrapper` in your console
    or simply add it to the config file.

    :param request: dict or request instance
    :return: request
    """
    if isinstance(request, dict):
        return fwk.DummyRequest(request)
    return request


def get_request_params(request: fwk.RequestType):
    """
    Returns a dictionary of the query parameters of the given request.

    :param request: any supported request
    :return: dictionary of parameters
    """
    supported_attrs = ("query_params", "GET", "args", "params")
    for attr in supported_attrs:
        if hasattr(request, attr):
            return getattr(request, attr)
    raise AttributeError(
        "Provided request object does not have any of the following attributes: "
        "{}.".format(", ".join(f"`{attr}`" for attr in supported_attrs))
    )


def dummify(request: fwk.Request) -> fwk.DummyRequest:
    """
    Constructs a :class:`qval.framework_integration.DummyRequest` with the parameters of the given request.

    :param request: any supported request
    :return: :code:`DummyRequest(request.<params>)`
    """
    return fwk.DummyRequest(get_request_params(request))


class FrozenBox(object):
    """
    A frozen dictionary that allows accessing the elements with :code:`.`

    Example:
        >>> box = FrozenBox({"num": 10, "s": "string"})
        >>> print(box.num, box.s)
        10 string
        >>> box["num"] = 404
        Traceback (most recent call last):
            ...
        TypeError: 'FrozenBox' object does not support item assignment
        >>> box.num = 404
        Traceback (most recent call last):
            ...
        TypeError: 'FrozenBox' object does not support attribute assignment
        >>> box.num
        10
    """

    def __init__(self, dct: Dict[Any, Any]):
        """
        :param dct: the dict to store
        """
        self.__dict__["__dct__"] = dct

    def __getitem__(self, item: str) -> Any:
        """
        [] operator.

        :param item:
        :return: value for the key `item`
        """
        return self.__dict__["__dct__"][item]

    def __getattr__(self, item: str) -> Any:
        """
        Returns the value of the stored `item` or attribute of the object.

        :param item: item key
        :return: value
        """
        return self[item]

    def __setattr__(self, key: str, value: str):
        """
        Raises TypeError.
        """
        raise TypeError(
            f"'{self.__class__.__name__}' object does not support attribute assignment"
        )

    def __contains__(self, item: str) -> bool:
        """
        Determines if the item is stored in the dictionary.

        :param item: item to check
        """
        return item in self.__dict__["__dct__"]

    def __iter__(self):
        """
        Returns an iterator over :code:`__dct__.items()`

        :return: :code:`iter(__dct__.items())`
        """
        return iter(self.__dict__["__dct__"].items())

    def __repr__(self) -> str:
        """
        Returns an evaluable representation of the :class:`FrozenBox` object.
        """
        return f"FrozenBox({self.__dict__['__dct__']})"

    def __str__(self) -> str:
        """
        Returns a string representation of the :class:`FrozenBox` object.

        :return: str(box)
        """
        return f"FrozenBox<{self.__dict__['__dct__']}>"


class ExcLogger(object):
    """
    A class used to report critical errors.

    >>> from qval.utils import log
    >>> log
    ExcLogger()
    >>> log.is_enabled
    True
    >>> log.disable()
    >>> print(log)
    ExcLogger<<Logger qval (WARNING)>>, enabled = false>
    """

    def __init__(self):
        """
        Instantiates the logger.

        :param logger: a list of loggers
        """
        self.logger = logging.getLogger("qval")
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        """
        Returns True if logging is enabled.
        """
        return self._enabled

    def disable(self):
        """
        Disables logging.

        :return: None
        """
        self._enabled = False

    def enable(self):
        """
        Enables logging.

        :return: None
        """
        self._enabled = True

    def log(self, level: str, *args, **kwargs):
        """
        Logs a new error message on the given level if logging is enabled.

        :param args: logger args
        :param kwargs: logger kwargs
        :return: None
        """
        if not self._enabled:
            return

        try:
            self.logger.log(level, *args, **kwargs)
        except Exception as e:
            self.logger.error(
                "Caught an error while logging with the parameters ({}, {}, {}):\n{}".format(
                    repr(level), args, kwargs, e
                )
            )

    def error(self, *args, **kwargs):
        """
        Shortcut for :meth:`log("error", ...) <qval.utils.ExcLogger.log>`.

        :param args: log args
        :param kwargs: log kwargs
        :return: None
        """
        self.log("error", *args, **kwargs)

    def __repr__(self) -> str:
        return "ExcLogger()"

    def __str__(self) -> str:
        return (
            f"ExcLogger<{self.logger}>, " f"enabled = {str(self.is_enabled).lower()}>"
        )


log = ExcLogger()
