from typing import Any, Callable

Predicate = Callable[[Any], bool]


class Validator(object):
    """
    Validates given value using provided predicates.
    """

    def __init__(self, *predicates: Predicate):
        # List of predicate functions
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
        Provides given value to the each predicate.

        :param value: value to validate
        :return: True if all checks are passed, False otherwise
        """
        for p in self.predicates:
            if not p(value):
                return False
        return True
