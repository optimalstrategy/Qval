import logging
from pprint import pformat
from typing import Dict, Any, List, Callable, Union

from . import framework_integration as fwk


@fwk._make_request
def make_request(request: Union[Dict[str, str], fwk.Request]) -> fwk.Request:
    """
    Creates DummyRequest if `request` is dictionary, and returns the `request` itself otherwise.
    :param request: dict or request instance
    :return: request
    """
    if isinstance(request, dict):
        return fwk.DummyRequest(request)
    return request


class FrozenBox(object):
    """
    Frozen dictionary that allows access to elements by `.`.
    """

    def __init__(self, dct: Dict[Any, Any]):
        """
        :param dct: dict to store
        """
        self.__dct__ = dct

    def __getitem__(self, item: str) -> Any:
        """
        [] operator.

        :param item: item key
        :return: value for key `item`
        """
        return self.__dct__[item]

    def __getattr__(self, item: str) -> Any:
        """
        Returns value of the stored `item` or attribute of the object.

        :param item: item key
        :return: value
        """
        if item == "__dct__":
            return getattr(super(), item)
        return self[item]

    def __contains__(self, item: str) -> bool:
        """
        Determines if item is inside of the dictionary.
        :param item: item to check
        """
        return item in self.__dct__

    def __iter__(self):
        """
        Returns iterator over self.__dct__.values()
        :return:
        """
        return iter(self.__dct__)

    def __repr__(self) -> str:
        """
        Returns evaluable representation of the FrozenBox object.
        """
        return f"FrozenBox({self.__dct__})"

    def __str__(self) -> str:
        """
        Returns string representation of the FrozenBox object.
        :return: str(box)
        """
        return f"FrozenBox<{self.__dct__}>"


class ExcLogger(object):
    """
    A class used in query parameters validation to report critical errors.
    """

    def __init__(self, logger_factories: List[Callable[[str], Any]]):
        """
        Instantiates the ExcLogger.
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
        Adds new logger factory to list.

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

    def error(self, name: str, *args, **kwargs):
        """
        Creates new logger using provided factories and dumps error message.

        :param name: logger name
        :param args: logger args
        :param kwargs: logger kwargs
        :return: None
        """
        if not self._enabled:
            return

        for log in self.factories:
            try:
                log(name).error(*args, **kwargs)
            except:
                pass

    @classmethod
    def detect_loggers(cls) -> "ExcLogger":
        """
        Looks for configuration and instantiates ExcLogger with detected loggers
        or default logging.getLogger
        :return: ExcLogger object
        """
        module = fwk.get_module()
        if hasattr(module, "QVAL_LOGGERS"):
            loggers = module.QVAL_LOGGERS
        else:
            loggers = [logging.getLogger]

        return cls(loggers)

    def __repr__(self) -> str:
        return f"ExcLogger([{', '.join(map(lambda x: x.__name__, self.factories))}])"

    def __str__(self) -> str:
        factories = pformat(str(self.factories)).strip("'")
        return f"ExcLogger({factories}, enabled = {self.is_enabled})"


# Detect loggers
log = ExcLogger.detect_loggers()

# Remove ExcLogger, this will make `log` acting as SingleTon
del ExcLogger
