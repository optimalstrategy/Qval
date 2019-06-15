from typing import Any, Callable, Union

Predicate = Callable[[Any], bool]


class QvalValidationError(Exception):
    """
    An error raised if validation fails.
    This exception should be used to provide a custom validation error message to the client.

    Example:
        >>> from qval import validate
        >>> def f(v: str) -> bool:
        ...     if not v.isnumeric():
        ...         raise QvalValidationError(f"Expected a number, got \'{v}\'")
        ...     return True
        >>> params = validate({"number": "42"}, {"number": f})
        >>> with params: pass  # OK
        >>> with params.apply_to_request({"number": "a string"}): pass
        Traceback (most recent call last):
            ...
        qval.exceptions.InvalidQueryParamException: ...
    """


class Validator(object):
    """
    Validates the given value using provided predicates.

    .. automethod:: __call__
    """

    # :class:`Validator` implements __call__(Any) -> bool, and
    # therefore can be treated in the same way as :type:`ValidatorType`.
    # For the sake of clarity, it is reflected in the class attributes below.
    ValidatorType = Union["Validator", Predicate]
    Predicate = ValidatorType

    def __init__(self, *predicates: Predicate):
        """
        Instantiates the validator.

        :param predicates: predefined predicates
        :type predicates: Callable[[Any], bool]
        """
        self.predicates = list(predicates)

    def add(self, predicate: Predicate) -> "Validator":
        """
        Adds the predicate to the list.

        :param predicate: predicate function
        :return: self
        """
        self.predicates.append(predicate)
        return self

    def __call__(self, value: Any) -> bool:
        """
        Applies all stored predicates to the given value.

        :param value: value to validate
        :return: True if all checks have passed, False otherwise
        """
        for p in self.predicates:
            if not p(value):
                return False
        return True
