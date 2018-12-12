from typing import Any, Callable

Predicate = Callable[[Any], bool]


class Validator(object):
    """
    Validates given value using provided predicates.

    .. automethod:: __call__
    """

    def __init__(self, *predicates: Predicate):
        """
        Instantiates the validator.

        :param predicates: predefined predicates
        :type predicates: Callable[[Any], bool]
        """
        self.predicates = list(predicates)

    def add(self, predicate: Predicate) -> "Validator":
        """
        Adds new predicate to the list.

        :param predicate: predicate function
        :return: self
        """
        self.predicates.append(predicate)
        return self

    def __call__(self, value: Any) -> bool:
        """
        Provides given value to each predicate.

        :param value: value to validate
        :return: True if all checks are passed, False otherwise
        """
        for p in self.predicates:
            if not p(value):
                return False
        return True
