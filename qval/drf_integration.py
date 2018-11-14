import logging
from typing import Union, Dict


class DummyRequest(object):
    """
    DummyRequest. Used for compatibility with DRF.
    """

    def __init__(self, params: Dict[str, str]):
        self.GET = params
        self.body = "<DummyRequest: no body>"

    @property
    def query_params(self) -> Dict[str, str]:
        """
        More semantically correct name for request.GET.
        """
        return self.GET


try:
    from rest_framework.request import Request
    from rest_framework.exceptions import APIException
    from rest_framework.status import (
        HTTP_400_BAD_REQUEST,
        HTTP_500_INTERNAL_SERVER_ERROR,
    )
except ImportError:
    logging.warning("Django Rest Framework is not installed, falling back to mocks.")

    # Define missing symbols
    class APIException(Exception):
        def __init__(self, detail: Union[dict, str]):
            self.detail = detail
            self.status_code = HTTP_500_INTERNAL_SERVER_ERROR
            super().__init__(str(detail))

    HTTP_400_BAD_REQUEST = 400
    HTTP_500_INTERNAL_SERVER_ERROR = 500

    # Define alias for compatibility
    Request = DummyRequest
