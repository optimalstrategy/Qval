from typing import Callable, Dict, Any, Iterable

from werkzeug.urls import url_encode
from qval.framework_integration import Request as ReqUnion


class RequestBuilder(object):
    def __init__(self):
        self.builders = {}

    def register(self, name: str, builder: Callable[[Dict[str, Any]], ReqUnion]):
        """
        Adds new callable to the request builder.

        :param name: name of the framework
        :param builder: builder callable
        :return: None
        """
        self.builders[name] = builder

    def build(self, name: str, params: Dict[str, Any]) -> ReqUnion:
        """
        Applies builder with name `name` to given params.

        :param name: name of the builder
        :param params: dict of query  params
        :return: built request class
        """
        return self.builders[name](params)

    def iterbuild(self, params: Dict[str, Any]) -> Iterable[ReqUnion]:
        """
        Builds and yield requests using saved builder.

        :param params: query params
        :return: Request classes
        """
        yield from (self.build(b, params) for b in self.builders)


builder = RequestBuilder()

try:
    import os
    import django.http
    from django.conf import settings, empty

    # Disable previously configured settings
    settings._wrapped = empty
    settings.configure()

    def build_django(params: Dict[str, Any]) -> django.http.HttpRequest:
        """
        Builds django.http.HttpRequest.

        :param params: query params
        :return: built request
        """
        r = django.http.HttpRequest()
        r.GET.update(params)
        return r

    builder.register("django", build_django)
except ImportError:
    pass

try:
    import rest_framework.request as drf

    def build_drf(params: Dict[str, Any]) -> drf.Request:
        """
        Builds rest_framework.request.Request.

        :param params: query params
        :return: built request
        """
        return drf.Request(build_django(params))

    builder.register("drf", build_drf)
except ImportError:
    pass


try:
    import flask

    def build_flask(params: Dict[str, Any]) -> flask.app.Request:
        """
        Builds flask.wrappers.Request

        :param params: query parameters
        :return: build request
        """
        query_string = url_encode(params)
        return flask.app.Request({"QUERY_STRING": query_string})

    builder.register("flask", build_flask)
except ImportError:
    pass

try:
    import falcon

    def build_falcon(params: Dict[str, Any]) -> falcon.Request:
        """
        Builds falcon.request.Request
        :param params:
        :return:
        """
        return falcon.Request(
            {
                "QUERY_STRING": url_encode(params),
                # avoid errors while printing
                "wsgi.input": None,
                "wsgi.errors": None,
                "wsgi.url_scheme": "https://",
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "test",
                "SERVER_NAME": "qvaltests",
                "SERVER_PORT": "433",
            }
        )

    builder.register("falcon", build_falcon)
except ImportError:
    pass
