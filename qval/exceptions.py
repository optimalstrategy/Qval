from typing import Union

from .drf_integration import APIException


class InvalidQueryParamException(APIException):
    """
    An error thrown when param fails the validation.
    """

    def __init__(self, detail: Union[dict, str], status: int):
        """
        :param detail: dict or string with details
        :param status: status code
        """
        super().__init__(detail)
        self.status_code = status
