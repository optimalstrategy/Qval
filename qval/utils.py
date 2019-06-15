import logging
from typing import Dict, Any, List, Callable, Union

from qval.framework_integration import load_symbol
from . import framework_integration as fwk


@fwk._make_request
def make_request(request: Union[Dict[str, str], fwk.Request]) -> fwk.RequestType:
    """
    Creates :class:`qval.framework_integration.DummyRequest`
    if :code:`request` is a dictionary, and returns the :code:`request` itself otherwise.

    Behavior of this function can be customized with the
    :func:`@_make_request() <qval.framework_integration._make_request>` decorator.
    Provide the path to your wrapper using :code:`QVAL_MAKE_REQUEST_WRAPPER` in the settings file
    or set it as an environment variable. The wrapper function must accept :code:`request` as a parameter and
    return an object that implements the request interface.

    For example, the following code adds print to each function call:
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
    Returns a dictionary of query parameters of the given request.

    :param request: any supported request
    :return: dictionary of parameters
    """
    supported_attrs = ("query_params", "GET", "args", "params")
    for attr in supported_attrs:
        if hasattr(request, attr):
            return getattr(request, attr)
    raise AttributeError(
        "Provided request object has no any of the following attributes: "
        "{}.".format(", ".join(f"`{attr}`" for attr in supported_attrs))
    )


def dummyfy(request: fwk.Request) -> fwk.DummyRequest:
    """
    Constructs :class:`qval.framework_integration.DummyRequest` with params of the given request.

    :param request: any supported request
    :return: :code:`DummyRequest(request.<params>)`
    """
    return fwk.DummyRequest(get_request_params(request))


class FrozenBox(object):
    """
    Frozen dictionary that allows accessing elements by :code:`.`

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
        :param dct: dict to store
        """
        self.__dict__["__dct__"] = dct

    def __getitem__(self, item: str) -> Any:
        """
        [] operator.

        :param item: item key
        :return: value for key `item`
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


# XXX: Think about removing this
class ExcLogger(object):
    """
    A class used to report critical errors.

    >>> from qval.utils import log
    >>> log
    ExcLogger([getLogger])
    >>> log.is_enabled
    True
    >>> log.disable()
    >>> print(log)
    ExcLogger<[getLogger], enabled = false>

    """

    def __init__(self, logger_factories: List[Callable[[str], Any]]):
        """
        Instantiates the logger.

        :param logger_factories: list of logger factories
        """
        self.factories = logger_factories
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

    def add_logger(self, log_factory: Callable[[str], Any]):
        """
        Adds new logger factory to the list.

        :param log_factory: logger
        :return: None
        """
        self.factories.append(log_factory)

    def clear(self):
        """
        Removes all saved factories.

        :return: None
        """
        self.factories.clear()

    def dump(self, name: str, level: str, *args, **kwargs):
        """
        Instantiates new loggers using configured factories and provides
        :code:`*args` and :code:`**kwargs` to the built objects.

        :param name: logger name
        :param level: logging level. If a built object has no attribute :code:`level`, it will be treated as callable.
        :param args: logger args
        :param kwargs: logger kwargs
        :return: None
        """
        if not self._enabled:
            return

        for build in self.factories:
            try:
                logger = build(name)
                if hasattr(logger, level):
                    getattr(logger, level)(*args, **kwargs)
                else:
                    logger(*args, **kwargs)
            except TypeError:
                raise
            except:  # lgtm [py/catch-base-exception]
                pass

    def error(self, name: str, *args, **kwargs):
        """
        Shortcut for :meth:`dump(name, "error", ...) <qval.utils.ExcLogger.dump>`.

        :param name: logger name
        :param args: logger args
        :param kwargs: logger kwargs
        :return: None
        """
        self.dump(name, "error", *args, **kwargs)

    @staticmethod
    def collect_loggers() -> list:
        """
        Looks for configuration and returns a list of detected loggers or :func:`logging.getLogger`.

        :return: list of collected loggers
        """
        module = fwk.get_module()
        if hasattr(module, "QVAL_LOGGERS"):
            _loggers = module.QVAL_LOGGERS
            if not isinstance(_loggers, (tuple, list)):
                _loggers = [_loggers]
            loggers = [load_symbol(log) for log in _loggers]
        else:
            loggers = [logging.getLogger]
        return loggers

    @classmethod
    def detect_loggers(cls, silent: bool = False) -> "ExcLogger":
        """
        Looks for configuration and instantiates ExcLogger with the detected loggers
        or default :func:`logging.getLogger`.

        :param silent: omit logging test message
        :return: ExcLogger object
        """
        logger = cls(cls.collect_loggers())
        if not silent:
            logger.dump(__file__, "info", "test message")
        return logger

    def __repr__(self) -> str:
        return f"ExcLogger([{', '.join(map(lambda x: x.__name__, self.factories))}])"

    def __str__(self) -> str:
        return (
            f"ExcLogger<[{', '.join(map(lambda x: x.__name__, self.factories))}], "
            f"enabled = {str(self.is_enabled).lower()}>"
        )


log = ExcLogger.detect_loggers()
